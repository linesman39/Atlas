"""The Field Agent (docs/project-definition.md, docs/requirements.md #1).

Extracts structured FieldNotes from a live session transcript: decisions,
constraints, files touched and why, abandoned expeditions, open
questions. This is genuinely an LLM extraction task — it needs to read
unstructured transcript segments and produce the typed FieldNote records
in atlas.models.

Deliberately not implemented in this pass: it requires a live connection
to the Claude Agent SDK (docs/architecture.md) and real session
transcripts to build and evaluate against — neither of which exists yet
in this repository. The interface below is the real contract; wiring it
to the SDK is the next piece of work, tracked in docs/requirements.md.
"""

from __future__ import annotations

from typing import Protocol

from atlas.models import FieldNote


class TranscriptSegment(Protocol):
    """Whatever shape a session transcript chunk takes — left abstract
    here so this module doesn't assume a specific harness's log format."""

    ...


def extract_field_notes(session_id: str, segment: TranscriptSegment) -> list[FieldNote]:
    """Extract structured FieldNotes from one new segment of a session
    transcript. Must run incrementally — see docs/requirements.md #1.
    """
    raise NotImplementedError(
        "Field Agent extraction requires a live Claude Agent SDK connection. "
        "See docs/architecture.md and docs/requirements.md #1."
    )
