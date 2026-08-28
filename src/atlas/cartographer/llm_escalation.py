"""The Cartographer's LLM escalation path — invoked only when
check_deterministic (deterministic.py) returns AMBIGUOUS: two facts share
a subject and scope but at least one is a narrative claim with no
structured value to compare mechanically.

Deliberately the smaller, secondary path. docs/competitive-landscape.md's
finding on "Don't Ask the LLM to Track Freshness" (arXiv 2606.01435) is
taken seriously here: this is reached only when the deterministic check
genuinely cannot resolve the question, not used as the default judge.

Runs against whatever LLMBackend it's given, defaulting to the engine's
free local backend — the Cartographer never assumes a paid API.
"""

from __future__ import annotations

from atlas.cartographer.deterministic import CheckResult, DeterministicVerdict
from atlas.llm import LLMBackend, extract_json, get_default_backend
from atlas.models import Fact

_SYSTEM_PROMPT = """You are the Cartographer in the Atlas project: you judge whether two claims about the same subject genuinely contradict each other, or can both be true at once.

Be conservative. Only call it a conflict if a reasonable engineer would say these cannot both hold simultaneously. Additional detail, a narrower scope, or a later refinement is not automatically a conflict.

Reply with ONLY JSON, no prose: {"conflict": true|false, "reason": "<one sentence>"}
"""


def escalate_to_llm(candidate: Fact, existing: Fact, backend: LLMBackend | None = None) -> DeterministicVerdict:
    backend = backend or get_default_backend()
    prompt = (
        f"Existing fact — subject: {existing.subject!r}, scope: {existing.scope!r}\n"
        f"Claim: {existing.claim}\n\n"
        f"Candidate fact — subject: {candidate.subject!r}, scope: {candidate.scope!r}\n"
        f"Claim: {candidate.claim}\n\n"
        "Do these genuinely conflict?"
    )
    result = backend.complete(_SYSTEM_PROMPT, prompt)
    data = extract_json(result.text)
    reason = f"[Cartographer LLM] {data.get('reason', '')}".strip()
    if data.get("conflict"):
        return DeterministicVerdict(result=CheckResult.LIKELY_CONFLICT, matched_fact_id=existing.id, reason=reason)
    return DeterministicVerdict(result=CheckResult.NO_CONFLICT, matched_fact_id=existing.id, reason=reason)
