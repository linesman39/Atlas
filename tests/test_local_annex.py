from pathlib import Path

from atlas.local_annex import annex_locally
from atlas.models import AnnexationVerdict, EvidenceKind, EvidenceRef, Fact
from atlas.storage import read_all_facts


def _grounded(**kwargs) -> Fact:
    kwargs.setdefault("evidence", [EvidenceRef(kind=EvidenceKind.DIFF, reference="x", summary="")])
    return Fact(**kwargs)


def test_approved_fact_gets_written_to_chart(tmp_path: Path):
    candidate = _grounded(subject="db_engine", scope="repo:a", claim="Uses Postgres.", value="postgres")
    decision = annex_locally(candidate, tmp_path)

    assert decision.verdict == AnnexationVerdict.APPROVED
    charted = read_all_facts(tmp_path)
    assert len(charted) == 1
    assert charted[0].id == candidate.id
    assert (tmp_path / "CHART.md").exists()


def test_disputed_fact_is_not_written(tmp_path: Path):
    existing = _grounded(subject="db_engine", scope="repo:a", claim="Uses Postgres.", value="postgres")
    annex_locally(existing, tmp_path)

    conflicting = _grounded(subject="db_engine", scope="repo:a", claim="Uses Redis.", value="redis")
    decision = annex_locally(conflicting, tmp_path)

    assert decision.verdict == AnnexationVerdict.DISPUTED
    charted = read_all_facts(tmp_path)
    assert len(charted) == 1  # the conflicting fact was never written
    assert charted[0].id == existing.id


def test_ungrounded_fact_is_rejected_and_not_written(tmp_path: Path):
    candidate = Fact(subject="x", scope="y", claim="no evidence attached")
    decision = annex_locally(candidate, tmp_path)

    assert decision.verdict == AnnexationVerdict.REJECTED_NO_EVIDENCE
    assert read_all_facts(tmp_path) == []
