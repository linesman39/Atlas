"""Scoring functions for the evaluation harness. Kept separate from
run.py so they're independently testable without invoking any agent."""

from __future__ import annotations

from rapidfuzz import fuzz

from atlas.eval.fixtures import SeededFieldNote
from atlas.models import FieldNote

MATCH_THRESHOLD = 65.0


def field_note_recall(extracted: list[FieldNote], seeded: list[SeededFieldNote]) -> dict:
    """What fraction of seeded ground-truth notes did extraction actually
    find? A seeded note counts as matched if some extracted note of the
    same category is fuzzy-similar enough — this is content recall, not
    exact-string matching, since a correct extraction won't always use
    identical wording."""
    if not seeded:
        # The "nothing worth recording" case: correct iff nothing was
        # extracted either. Recall of an empty set is vacuously 1.0, but
        # we still want to penalize padding, so report it as a separate
        # signal rather than silently calling it perfect.
        return {
            "seeded": 0,
            "matched": 0,
            "recall": 1.0,
            "extracted_total": len(extracted),
            "correctly_empty": len(extracted) == 0,
        }

    matched = 0
    for s in seeded:
        same_category = [e for e in extracted if e.category == s.category]
        best = max((fuzz.token_sort_ratio(s.content.lower(), e.content.lower()) for e in same_category), default=0)
        if best >= MATCH_THRESHOLD:
            matched += 1

    return {
        "seeded": len(seeded),
        "matched": matched,
        "recall": matched / len(seeded),
        "extracted_total": len(extracted),
        "correctly_empty": False,
    }
