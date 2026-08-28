"""Core data model. Every fact Atlas ever records is one of these — a typed
record, not prose, because the Cartographer's deterministic check needs
something it can compare without an LLM.

See docs/lexicon.md for the vocabulary and docs/architecture.md for why
this shape (Pydantic, not a vector/graph store) was chosen.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class Tier(str, Enum):
    """Where a fact lives. See docs/lexicon.md: Field Notes / Chart / Atlas."""

    FIELD_NOTES = "field_notes"
    CHART = "chart"
    ATLAS = "atlas"


class FactStatus(str, Enum):
    PROPOSED = "proposed"
    ANNEXED = "annexed"
    DISPUTED = "disputed"
    RETRACTED = "retracted"


class EvidenceKind(str, Enum):
    TEST_RESULT = "test_result"
    DIFF = "diff"
    COMMAND_OUTPUT = "command_output"


class EvidenceRef(BaseModel):
    """A pointer to something real that backs a fact. No fact may be
    annexed without at least one of these — see docs/requirements.md,
    "Ground-truthing"."""

    kind: EvidenceKind
    reference: str = Field(description="Path, URL, commit SHA, or command that produced this evidence")
    captured_at: datetime = Field(default_factory=_now)
    summary: str = Field(default="", description="One line: what the evidence shows")


class Fact(BaseModel):
    """The atomic unit of record — a Survey's output (docs/lexicon.md)."""

    id: str = Field(default_factory=_new_id)
    subject: str = Field(description='What this fact is about, e.g. "library:redis" or "module:auth"')
    scope: str = Field(description='Where it applies, e.g. a repo name, or "global" for Atlas-tier facts')
    claim: str = Field(description="The human-readable statement of what's true")
    value: str | None = Field(
        default=None,
        description=(
            "Structured value for key-value-shaped facts (e.g. subject='db_engine', "
            "value='postgres'). Enables deterministic contradiction detection. "
            "Leave None for narrative constraints that can't be reduced to a single value."
        ),
    )
    tier: Tier = Tier.FIELD_NOTES
    status: FactStatus = FactStatus.PROPOSED
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    supersedes: str | None = Field(default=None, description="id of a Fact this one retracts or replaces")
    shareable: bool = Field(default=False, description="Eligible for a trade route (cross-org annexation)")
    created_at: datetime = Field(default_factory=_now)
    last_verified: datetime | None = Field(default=None, description="Last time Weathering re-checked this fact")

    def is_ground_truthed(self) -> bool:
        """A fact may only be annexed if it's backed by real evidence."""
        return len(self.evidence) > 0


class FieldNoteCategory(str, Enum):
    DECISION = "decision"
    CONSTRAINT = "constraint"
    REJECTED_APPROACH = "rejected_approach"
    OPEN_QUESTION = "open_question"


class FieldNote(BaseModel):
    """Raw output of the Field Agent, before the Cartographer sees it."""

    id: str = Field(default_factory=_new_id)
    session_id: str
    category: FieldNoteCategory
    content: str
    evidence: list[EvidenceRef] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)


class BorderDispute(BaseModel):
    """Two facts claim contradictory things about the same territory."""

    id: str = Field(default_factory=_new_id)
    existing_fact_id: str
    candidate_fact_id: str
    reason: str
    detected_by: str = Field(description='"deterministic" or "cartographer_llm"')
    resolved: bool = False
    resolution: str | None = None


class AnnexationVerdict(str, Enum):
    APPROVED = "approved"
    DISPUTED = "disputed"
    REJECTED_NO_EVIDENCE = "rejected_no_evidence"


class AnnexationRequest(BaseModel):
    """A candidate fact's journey from Field Notes toward a Chart or the Atlas."""

    id: str = Field(default_factory=_new_id)
    fact: Fact
    target_tier: Tier
    verdict: AnnexationVerdict | None = None
    dispute: BorderDispute | None = None
    pr_url: str | None = None
    created_at: datetime = Field(default_factory=_now)
