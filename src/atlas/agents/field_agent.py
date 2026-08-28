"""The Field Agent (docs/project-definition.md, docs/requirements.md #1).

Extracts structured FieldNotes from a session transcript segment:
decisions, constraints, rejected approaches, open questions. Deliberately
conservative — instructed not to infer anything not explicitly stated,
because everything it produces feeds into the Cartographer, and a
hallucinated Field Note is the single easiest way to poison a Chart.

Runs against whatever LLMBackend it's given, defaulting to the engine's
free local backend (atlas.llm.get_default_backend) — never assumes a
paid API is available.
"""

from __future__ import annotations

from atlas.llm import LLMBackend, extract_json, get_default_backend
from atlas.models import FieldNote, FieldNoteCategory

_SYSTEM_PROMPT = """You are the Field Agent in the Atlas project: you take field notes on a coding-agent session in progress.

Given a segment of a session transcript, extract every decision, constraint, rejected approach, and open question that is EXPLICITLY stated in it. Do not infer anything that isn't directly said. Do not invent details. If nothing worth recording appears, that's a correct and expected answer — don't manufacture content to fill the response.

Reply with ONLY a JSON array, no prose, no code fences. Each element:
{"category": "decision"|"constraint"|"rejected_approach"|"open_question", "content": "<one clear, self-contained sentence>"}

Empty array if nothing qualifies: []
"""


def extract_field_notes(
    session_id: str,
    transcript_segment: str,
    backend: LLMBackend | None = None,
) -> list[FieldNote]:
    """Extract structured FieldNotes from one new segment of a session
    transcript. Intended to be called incrementally as new segments
    arrive, not on a full transcript replay each time."""
    backend = backend or get_default_backend()
    result = backend.complete(_SYSTEM_PROMPT, transcript_segment)
    items = extract_json(result.text)
    notes = []
    for item in items:
        notes.append(
            FieldNote(
                session_id=session_id,
                category=FieldNoteCategory(item["category"]),
                content=item["content"],
            )
        )
    return notes
