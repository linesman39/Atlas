import subprocess
import sys
from pathlib import Path

from atlas.models import EvidenceKind, EvidenceRef, Fact
from atlas.storage import write_fact


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


def test_cli_exits_zero_when_nothing_stale(tmp_path: Path):
    repo = _init_repo(tmp_path)
    chart_dir = tmp_path / "chart"
    sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    write_fact(
        Fact(subject="x", scope="y", claim="z", evidence=[EvidenceRef(kind=EvidenceKind.DIFF, reference=sha, summary="")]),
        chart_dir,
    )

    result = subprocess.run(
        [sys.executable, "-m", "atlas.weathering", str(chart_dir), str(repo)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "0 newly disputed" in result.stdout


def test_cli_exits_nonzero_when_something_stale(tmp_path: Path):
    repo = _init_repo(tmp_path)
    chart_dir = tmp_path / "chart"
    write_fact(
        Fact(subject="x", scope="y", claim="z", evidence=[EvidenceRef(kind=EvidenceKind.DIFF, reference="0" * 40, summary="")]),
        chart_dir,
    )

    result = subprocess.run(
        [sys.executable, "-m", "atlas.weathering", str(chart_dir), str(repo)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "1 newly disputed" in result.stdout
    assert "[STALE]" in result.stdout


def test_cli_handles_empty_chart_gracefully(tmp_path: Path):
    chart_dir = tmp_path / "empty_chart"
    chart_dir.mkdir()
    repo = _init_repo(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "atlas.weathering", str(chart_dir), str(repo)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "nothing to weather" in result.stdout
