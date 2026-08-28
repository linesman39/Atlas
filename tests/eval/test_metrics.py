from atlas.eval.fixtures import SeededFieldNote
from atlas.eval.metrics import field_note_recall
from atlas.models import FieldNote, FieldNoteCategory


def _note(category: FieldNoteCategory, content: str) -> FieldNote:
    return FieldNote(session_id="s", category=category, content=content)


def test_perfect_recall():
    seeded = [SeededFieldNote(category=FieldNoteCategory.DECISION, content="Switched to Postgres.")]
    extracted = [_note(FieldNoteCategory.DECISION, "Switched to Postgres.")]
    result = field_note_recall(extracted, seeded)
    assert result["recall"] == 1.0
    assert result["matched"] == 1


def test_fuzzy_match_counts():
    seeded = [SeededFieldNote(category=FieldNoteCategory.DECISION, content="Switched session storage from Redis to Postgres.")]
    extracted = [_note(FieldNoteCategory.DECISION, "The team decided to switch session storage from Redis to Postgres.")]
    result = field_note_recall(extracted, seeded)
    assert result["matched"] == 1


def test_wrong_category_does_not_match():
    seeded = [SeededFieldNote(category=FieldNoteCategory.DECISION, content="Switched to Postgres.")]
    extracted = [_note(FieldNoteCategory.OPEN_QUESTION, "Switched to Postgres.")]
    result = field_note_recall(extracted, seeded)
    assert result["matched"] == 0
    assert result["recall"] == 0.0


def test_missed_note_lowers_recall():
    seeded = [
        SeededFieldNote(category=FieldNoteCategory.DECISION, content="Switched to Postgres."),
        SeededFieldNote(category=FieldNoteCategory.OPEN_QUESTION, content="Should we alert on Redis memory?"),
    ]
    extracted = [_note(FieldNoteCategory.DECISION, "Switched to Postgres.")]
    result = field_note_recall(extracted, seeded)
    assert result["matched"] == 1
    assert result["recall"] == 0.5


def test_empty_seeded_and_empty_extracted_is_correctly_empty():
    result = field_note_recall([], [])
    assert result["recall"] == 1.0
    assert result["correctly_empty"] is True


def test_empty_seeded_but_extracted_something_flags_not_correctly_empty():
    result = field_note_recall([_note(FieldNoteCategory.DECISION, "invented")], [])
    assert result["correctly_empty"] is False
