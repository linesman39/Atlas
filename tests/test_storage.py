from pathlib import Path

from atlas.models import EvidenceKind, EvidenceRef, Fact
from atlas.storage import build_index, markdown_to_fact, read_all_facts, write_fact, write_index


def _sample_fact() -> Fact:
    return Fact(
        subject="db_engine",
        scope="repo:payments-api",
        claim="This service uses Postgres, not MySQL, because of the JSONB columns in the ledger table.",
        value="postgres",
        evidence=[EvidenceRef(kind=EvidenceKind.DIFF, reference="abc123", summary="migration to JSONB ledger")],
    )


def test_round_trip(tmp_path: Path):
    fact = _sample_fact()
    path = write_fact(fact, tmp_path)
    assert path.exists()

    loaded = markdown_to_fact(path.read_text())
    assert loaded.id == fact.id
    assert loaded.subject == fact.subject
    assert loaded.value == fact.value
    assert loaded.claim.strip() == fact.claim.strip()
    assert len(loaded.evidence) == 1


def test_read_all_facts_skips_index(tmp_path: Path):
    fact = _sample_fact()
    write_fact(fact, tmp_path)
    write_index([fact], tmp_path, title="The Chart")

    facts = read_all_facts(tmp_path)
    assert len(facts) == 1
    assert facts[0].id == fact.id


def test_index_flags_missing_evidence():
    ungrounded = Fact(subject="library:foo", scope="global", claim="Some claim with no evidence.")
    index = build_index([ungrounded], title="The Atlas")
    assert "NO EVIDENCE" in index
