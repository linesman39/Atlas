"""Hand-authored synthetic scenarios with seeded ground truth — deliberately
not LLM-generated. docs/project-definition.md's evaluation design exists
specifically to avoid the integrity problems documented in
docs/competitive-landscape.md (the public Mem0/Zep benchmark dispute,
LOCOMO's dropped-refusal-questions flaw): self-controlled ground truth a
human wrote and labeled, not borrowed or auto-generated.
"""

from __future__ import annotations

from pydantic import BaseModel

from atlas.models import EvidenceKind, EvidenceRef, Fact, FieldNoteCategory


class SeededFieldNote(BaseModel):
    category: FieldNoteCategory
    content: str


class FieldAgentScenario(BaseModel):
    name: str
    transcript_segment: str
    seeded_notes: list[SeededFieldNote]


class CartographerCase(BaseModel):
    name: str
    existing: Fact
    candidate: Fact
    expect_conflict: bool  # human-labeled ground truth


def _grounded(**kwargs) -> Fact:
    kwargs.setdefault("evidence", [EvidenceRef(kind=EvidenceKind.DIFF, reference="fixture", summary="")])
    return Fact(**kwargs)


FIELD_AGENT_SCENARIOS: list[FieldAgentScenario] = [
    FieldAgentScenario(
        name="redis_to_postgres",
        transcript_segment=(
            "User: The payments service keeps dropping sessions under load. Can you look into it?\n\n"
            "Assistant: I checked the load test results — the session store is backed by Redis, "
            "and it's evicting keys under memory pressure because no maxmemory-policy was set. "
            "I tried switching to Postgres-backed sessions instead and re-ran the load test: "
            "zero drops at 500 concurrent sessions. I'm not touching the auth module itself "
            "since that's out of scope for this fix. One open question: should we also add "
            "a Redis maxmemory alert for other services that still use it?"
        ),
        seeded_notes=[
            SeededFieldNote(category=FieldNoteCategory.DECISION, content="Switched session storage from Redis to Postgres."),
            SeededFieldNote(category=FieldNoteCategory.CONSTRAINT, content="Did not modify the auth module — out of scope."),
            SeededFieldNote(category=FieldNoteCategory.OPEN_QUESTION, content="Should a Redis maxmemory alert be added for other services?"),
        ],
    ),
    FieldAgentScenario(
        name="rejected_orm_migration",
        transcript_segment=(
            "User: can we migrate off the raw SQL queries to an ORM?\n\n"
            "Assistant: I tried migrating the reporting module to SQLAlchemy first as a trial. "
            "It regressed query performance by roughly 3x on the largest report because the ORM "
            "generated N+1 queries we hadn't hit before. I reverted that change and I'm keeping "
            "raw SQL for the reporting module specifically. Other modules weren't affected by "
            "this finding and are still candidates for a future migration."
        ),
        seeded_notes=[
            SeededFieldNote(category=FieldNoteCategory.REJECTED_APPROACH, content="Tried migrating the reporting module to SQLAlchemy; reverted due to N+1 queries causing a 3x performance regression."),
            SeededFieldNote(category=FieldNoteCategory.CONSTRAINT, content="Reporting module keeps raw SQL, not an ORM."),
        ],
    ),
    FieldAgentScenario(
        name="nothing_worth_recording",
        # The challenging case: a segment with real conversation but nothing
        # that meets the bar (nothing explicitly decided, constrained,
        # rejected, or left open). Correct output is an empty list — a
        # Field Agent that pads output to seem useful fails this case even
        # though a human skimming it would agree there's nothing to note.
        transcript_segment=(
            "User: can you show me what's in the utils folder?\n\n"
            "Assistant: Sure — it has string_helpers.py, date_helpers.py, and a small __init__.py "
            "that just re-exports both."
        ),
        seeded_notes=[],
    ),
]


CARTOGRAPHER_CASES: list[CartographerCase] = [
    CartographerCase(
        name="deterministic_conflict",
        existing=_grounded(subject="db_engine", scope="repo:payments-api", claim="Uses Postgres.", value="postgres"),
        candidate=_grounded(subject="db_engine", scope="repo:payments-api", claim="Uses Redis.", value="redis"),
        expect_conflict=True,
    ),
    CartographerCase(
        name="deterministic_corroboration",
        existing=_grounded(subject="db_engine", scope="repo:payments-api", claim="Uses Postgres.", value="postgres"),
        candidate=_grounded(subject="db_engine", scope="repo:payments-api", claim="Confirmed Postgres again.", value="postgres"),
        expect_conflict=False,
    ),
    CartographerCase(
        name="ambiguous_genuine_conflict",
        existing=_grounded(subject="module:auth", scope="repo:payments-api", claim="Auth module uses session cookies exclusively."),
        candidate=_grounded(subject="module:auth", scope="repo:payments-api", claim="Session cookies were removed entirely; auth is now JWT-only."),
        expect_conflict=True,
    ),
    CartographerCase(
        name="ambiguous_compatible_addition",
        existing=_grounded(subject="module:auth", scope="repo:payments-api", claim="Auth module supports session cookies for the web client."),
        candidate=_grounded(subject="module:auth", scope="repo:payments-api", claim="Auth module also now supports JWT for the mobile client, alongside existing session cookies."),
        expect_conflict=False,
    ),
    CartographerCase(
        name="different_scope_not_a_conflict",
        existing=_grounded(subject="db_engine", scope="repo:payments-api", claim="Uses Postgres.", value="postgres"),
        candidate=_grounded(subject="db_engine", scope="repo:reporting-api", claim="Uses Redis.", value="redis"),
        expect_conflict=False,
    ),
]
