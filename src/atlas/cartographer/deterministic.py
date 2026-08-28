"""The Cartographer's deterministic-first check (docs/architecture.md,
docs/requirements.md #2).

Honesty constraint: this must actually be deterministic, not a semantic
model wearing a deterministic label. That means it can only resolve a
conflict without an LLM when both facts reduce to a comparable structured
value. Everything else — two narrative claims about the same subject that
might or might not actually contradict — is correctly AMBIGUOUS and must
be escalated to an LLM judgment (not implemented in this module; see
atlas/cartographer/llm.py, not yet built).

This is the finding from docs/competitive-landscape.md taken seriously:
"Don't Ask the LLM to Track Freshness" (arXiv 2606.01435) argues pure
LLM-judged conflict tracking is unreliable — so this module's whole job
is to shrink how often an LLM has to be asked at all.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel
from rapidfuzz import fuzz

from atlas.models import Fact

DEFAULT_SUBJECT_MATCH_THRESHOLD = 90.0


class CheckResult(str, Enum):
    NO_CONFLICT = "no_conflict"
    LIKELY_CONFLICT = "likely_conflict"
    AMBIGUOUS = "ambiguous"  # needs the Cartographer's LLM judgment


class DeterministicVerdict(BaseModel):
    result: CheckResult
    matched_fact_id: str | None = None
    reason: str


def _same_territory(candidate: Fact, existing: Fact, threshold: float) -> bool:
    if candidate.scope != existing.scope:
        return False
    return fuzz.token_sort_ratio(candidate.subject.lower(), existing.subject.lower()) >= threshold


def check_deterministic(
    candidate: Fact,
    existing_facts: list[Fact],
    threshold: float = DEFAULT_SUBJECT_MATCH_THRESHOLD,
) -> DeterministicVerdict:
    """Check a candidate fact against everything already charted for the
    same subject and scope.

    - No existing fact about this subject/scope -> NO_CONFLICT (new territory).
    - An existing fact with the same structured `value` -> NO_CONFLICT (corroboration).
    - An existing fact with a *different* structured `value` -> LIKELY_CONFLICT,
      resolved without an LLM because both sides reduce to a comparable value.
    - An existing fact where either side has no structured `value` (a
      narrative claim) -> AMBIGUOUS. Whether "the auth module now uses JWT"
      contradicts "the auth module uses session cookies" requires reading
      comprehension this function deliberately does not attempt.
    """
    matches = [f for f in existing_facts if f.id != candidate.id and _same_territory(candidate, f, threshold)]

    if not matches:
        return DeterministicVerdict(result=CheckResult.NO_CONFLICT, reason="No existing fact for this subject/scope.")

    for existing in matches:
        if candidate.value is not None and existing.value is not None:
            if candidate.value.strip().lower() == existing.value.strip().lower():
                return DeterministicVerdict(
                    result=CheckResult.NO_CONFLICT,
                    matched_fact_id=existing.id,
                    reason=f"Corroborates existing fact {existing.id} (same value: {existing.value!r}).",
                )
            return DeterministicVerdict(
                result=CheckResult.LIKELY_CONFLICT,
                matched_fact_id=existing.id,
                reason=(
                    f"Contradicts existing fact {existing.id}: "
                    f"{existing.value!r} -> {candidate.value!r} for the same subject/scope."
                ),
            )

    # At least one side of every match is a narrative claim with no
    # structured value — can't resolve deterministically.
    return DeterministicVerdict(
        result=CheckResult.AMBIGUOUS,
        matched_fact_id=matches[0].id,
        reason=(
            f"Existing fact {matches[0].id} covers the same subject/scope but at least one "
            "side has no structured value — needs the Cartographer's LLM judgment."
        ),
    )
