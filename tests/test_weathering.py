import subprocess
from pathlib import Path

from atlas.models import EvidenceKind, EvidenceRef, Fact, FactStatus
from atlas.storage import read_all_facts, write_fact
from atlas.weathering import reverify_chart, reverify_evidence


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    (repo / "app.py").write_text("print('hi')\n")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def test_diff_evidence_confirmed_when_commit_exists(tmp_path: Path):
    repo = _init_repo(tmp_path)
    sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    valid, reason = reverify_evidence(EvidenceRef(kind=EvidenceKind.DIFF, reference=sha, summary=""), repo)
    assert valid is True
    assert sha in reason


def test_diff_evidence_fails_when_commit_absent(tmp_path: Path):
    repo = _init_repo(tmp_path)
    valid, reason = reverify_evidence(
        EvidenceRef(kind=EvidenceKind.DIFF, reference="0" * 40, summary=""), repo
    )
    assert valid is False


def test_test_result_evidence_checks_file_existence(tmp_path: Path):
    repo = _init_repo(tmp_path)
    (repo / "tests_dir").mkdir()
    (repo / "tests_dir" / "test_x.py").write_text("def test_x(): pass\n")

    valid, _ = reverify_evidence(
        EvidenceRef(kind=EvidenceKind.TEST_RESULT, reference="tests_dir/test_x.py::test_x", summary=""), repo
    )
    assert valid is True

    valid, _ = reverify_evidence(
        EvidenceRef(kind=EvidenceKind.TEST_RESULT, reference="tests_dir/gone.py::test_x", summary=""), repo
    )
    assert valid is False


def test_command_output_is_not_auto_verifiable(tmp_path: Path):
    repo = _init_repo(tmp_path)
    valid, reason = reverify_evidence(
        EvidenceRef(kind=EvidenceKind.COMMAND_OUTPUT, reference="npm test", summary=""), repo
    )
    assert valid is None
    assert "cannot be automatically" in reason


def test_reverify_chart_disputes_facts_with_stale_evidence(tmp_path: Path):
    repo = _init_repo(tmp_path)
    chart_dir = tmp_path / "chart"

    stale = Fact(
        subject="module:x",
        scope="repo:a",
        claim="Old claim.",
        evidence=[EvidenceRef(kind=EvidenceKind.DIFF, reference="0" * 40, summary="")],
    )
    write_fact(stale, chart_dir)

    fresh_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    fresh = Fact(
        subject="module:y",
        scope="repo:a",
        claim="Current claim.",
        evidence=[EvidenceRef(kind=EvidenceKind.DIFF, reference=fresh_sha, summary="")],
    )
    write_fact(fresh, chart_dir)

    results = reverify_chart(chart_dir, repo)
    by_subject = {r.subject: r for r in results}
    assert by_subject["module:x"].still_valid is False
    assert by_subject["module:y"].still_valid is True

    updated = {f.subject: f for f in read_all_facts(chart_dir)}
    assert updated["module:x"].status == FactStatus.DISPUTED
    assert updated["module:x"].last_verified is not None
    assert updated["module:y"].status != FactStatus.DISPUTED
