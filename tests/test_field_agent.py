from atlas.agents.field_agent import extract_field_notes
from atlas.models import FieldNoteCategory
from tests.fakes import FakeBackend


def test_extract_field_notes_parses_backend_response():
    fake = FakeBackend(
        response_text="""[
          {"category": "decision", "content": "Switched session storage from Redis to Postgres."},
          {"category": "open_question", "content": "Should we alert on Redis maxmemory for other services?"}
        ]"""
    )
    notes = extract_field_notes("session-1", "some transcript segment", backend=fake)

    assert len(notes) == 2
    assert notes[0].category == FieldNoteCategory.DECISION
    assert notes[1].category == FieldNoteCategory.OPEN_QUESTION
    assert notes[0].session_id == "session-1"
    # the transcript segment is what gets sent as the user prompt
    assert fake.calls[0][1] == "some transcript segment"


def test_extract_field_notes_handles_empty_result():
    fake = FakeBackend(response_text="[]")
    notes = extract_field_notes("session-1", "nothing interesting happened", backend=fake)
    assert notes == []
