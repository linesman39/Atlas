"""The Cartographer's full annexation check — the single entrypoint Chart
Keeper and Atlas Keeper call before ever proposing an annexation. Order
matters and is deliberate: ground-truthing first (an unproven fact never
even reaches conflict-checking), then the free deterministic check, and
only then the LLM, so the expensive path is the last resort, not the
default.
"""

from __future__ import annotations

from pydantic import BaseModel

from atlas.cartographer.deterministic import CheckResult, check_deterministic
from atlas.cartographer.llm_escalation import escalate_to_llm
from atlas.llm import LLMBackend
from atlas.models import AnnexationVerdict, BorderDispute, Fact


class CartographerDecision(BaseModel):
    verdict: AnnexationVerdict
    dispute: BorderDispute | None = None
    reason: str = ""


def evaluate(
    candidate: Fact,
    existing_facts: list[Fact],
    use_llm_escalation: bool = True,
    backend: LLMBackend | None = None,
) -> CartographerDecision:
    if not candidate.is_ground_truthed():
        return CartographerDecision(
            verdict=AnnexationVerdict.REJECTED_NO_EVIDENCE,
            reason="No evidence attached — see docs/requirements.md, Ground-truthing.",
        )

    det = check_deterministic(candidate, existing_facts)

    if det.result == CheckResult.NO_CONFLICT:
        return CartographerDecision(verdict=AnnexationVerdict.APPROVED, reason=det.reason)

    matched = next(f for f in existing_facts if f.id == det.matched_fact_id)

    if det.result == CheckResult.LIKELY_CONFLICT:
        dispute = BorderDispute(
            existing_fact_id=matched.id,
            candidate_fact_id=candidate.id,
            reason=det.reason,
            detected_by="deterministic",
        )
        return CartographerDecision(verdict=AnnexationVerdict.DISPUTED, dispute=dispute, reason=det.reason)

    # AMBIGUOUS
    if not use_llm_escalation:
        dispute = BorderDispute(
            existing_fact_id=matched.id,
            candidate_fact_id=candidate.id,
            reason=det.reason,
            detected_by="deterministic",
        )
        return CartographerDecision(
            verdict=AnnexationVerdict.DISPUTED, dispute=dispute, reason=det.reason + " (LLM escalation disabled)"
        )

    llm_verdict = escalate_to_llm(candidate, matched, backend=backend)
    if llm_verdict.result == CheckResult.LIKELY_CONFLICT:
        dispute = BorderDispute(
            existing_fact_id=matched.id,
            candidate_fact_id=candidate.id,
            reason=llm_verdict.reason,
            detected_by="cartographer_llm",
        )
        return CartographerDecision(verdict=AnnexationVerdict.DISPUTED, dispute=dispute, reason=llm_verdict.reason)
    return CartographerDecision(verdict=AnnexationVerdict.APPROVED, reason=llm_verdict.reason)
