"""Live, real end-to-end proof that the LLM-backed agents work.

Not part of `pytest` — a live model, local or hosted, is genuinely
required, so this stays a manual script rather than a CI test. Uses
whatever ATLAS_LLM_BACKEND resolves to (default: "local", i.e. Ollama —
see docs/architecture.md, "Engine vs. Application"). Run manually:

    source .venv/bin/activate
    ollama pull llama3.1   # once, if you haven't already
    python3 scripts/live_smoke_test.py

    # or, to use the optional hosted backend instead:
    ATLAS_LLM_BACKEND=claude python3 scripts/live_smoke_test.py

Prints a full trajectory (what each agent was given, what it produced,
what it cost) so the output can be captured into docs/trajectories/.
"""

from __future__ import annotations

from atlas.agents.briefing_agent import draft_briefing_for_agent, draft_briefing_for_human
from atlas.agents.field_agent import extract_field_notes
from atlas.cartographer.evaluate import evaluate
from atlas.models import EvidenceKind, EvidenceRef, Fact

TRANSCRIPT_SEGMENT = """
User: The payments service keeps dropping sessions under load. Can you look into it?

Assistant: I checked the load test results — the session store is backed by Redis,
and it's evicting keys under memory pressure because no maxmemory-policy was set.
I tried switching to Postgres-backed sessions instead and re-ran the load test:
zero drops at 500 concurrent sessions. I'm not touching the auth module itself
since that's out of scope for this fix. One open question: should we also add
a Redis maxmemory alert for other services that still use it?
""".strip()


def main() -> None:
    total_cost = 0.0

    print("=== Field Agent: extracting Field Notes from a transcript segment ===")
    notes = extract_field_notes(session_id="demo-session-1", transcript_segment=TRANSCRIPT_SEGMENT)
    for n in notes:
        print(f"  [{n.category.value}] {n.content}")
    print(f"  -> {len(notes)} field note(s) extracted\n")

    print("=== Cartographer: evaluating an AMBIGUOUS annexation (needs LLM escalation) ===")
    existing = Fact(
        subject="module:session_store",
        scope="repo:payments-api",
        claim="Session storage is backed by Redis.",
        evidence=[EvidenceRef(kind=EvidenceKind.DIFF, reference="prior-commit", summary="original Redis setup")],
    )
    candidate = Fact(
        subject="module:session_store",
        scope="repo:payments-api",
        claim="Session storage is now backed by Postgres; Redis dropped sessions under load.",
        evidence=[
            EvidenceRef(
                kind=EvidenceKind.TEST_RESULT,
                reference="load_test_2026_08_28",
                summary="0 dropped sessions at 500 concurrent, vs. failures on Redis",
            )
        ],
    )
    decision = evaluate(candidate, existing_facts=[existing])
    print(f"  verdict: {decision.verdict.value}")
    print(f"  reason: {decision.reason}")
    if decision.dispute:
        print(f"  dispute detected_by: {decision.dispute.detected_by}")
    print()

    print("=== Briefing Agent: drafting Expedition Briefings ===")
    facts = [existing, candidate]
    human_brief = draft_briefing_for_human(facts)
    print("--- for a human ---")
    print(human_brief)
    print()

    agent_brief = draft_briefing_for_agent(facts)
    print("--- for a fresh agent ---")
    print(agent_brief)


if __name__ == "__main__":
    main()
