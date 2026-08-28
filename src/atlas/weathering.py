"""Weathering: re-verification of already-annexed facts. Not a new agent
— the Cartographer's own evidence discipline, run on a schedule against
facts already in a Chart, rather than only at annexation time. See
docs/architecture.md, "Committed beyond today's build".

Honest scope limit: this checks whether the referenced evidence artifact
still *exists* (a git object, a test file) — it does not re-execute a
test suite, since that requires knowing the project's test framework and
runner, which this generic module has no way to know. A real CI-wired
weathering job should re-run the actual tests and pass the outcome in;
this module is the static-existence check that works for any repo with
no configuration.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from atlas.models import EvidenceKind, EvidenceRef, Fact, FactStatus
from atlas.storage import read_all_facts, write_fact, write_index


class ReverificationResult(BaseModel):
    fact_id: str
    subject: str
    still_valid: bool
    reason: str


def reverify_evidence(evidence: EvidenceRef, repo_root: Path) -> tuple[bool | None, str]:
    """Returns (still_valid, reason). still_valid is None when this kind
    of evidence has no generic way to be automatically re-checked."""
    if evidence.kind == EvidenceKind.DIFF:
        result = subprocess.run(
            ["git", "cat-file", "-e", evidence.reference],
            cwd=repo_root,
            capture_output=True,
        )
        if result.returncode == 0:
            return True, f"git object {evidence.reference!r} still exists"
        return False, f"git object {evidence.reference!r} no longer exists in this repo"

    if evidence.kind == EvidenceKind.TEST_RESULT:
        file_part = evidence.reference.split("::")[0]
        path = repo_root / file_part
        if path.exists():
            return True, f"referenced test file {file_part!r} still exists (not re-executed)"
        return False, f"referenced test file {file_part!r} no longer exists"

    return None, "command_output evidence cannot be automatically re-verified — needs a real re-run"


def reverify_chart(chart_dir: Path, repo_root: Path) -> list[ReverificationResult]:
    """Re-check every fact in a Chart. A fact with at least one confirmed
    piece of evidence stays valid; a fact where every checkable piece of
    evidence has gone stale is marked DISPUTED, not silently dropped —
    a human still decides whether to retract it."""
    facts = read_all_facts(chart_dir)
    results: list[ReverificationResult] = []

    for fact in facts:
        if not fact.evidence:
            results.append(
                ReverificationResult(fact_id=fact.id, subject=fact.subject, still_valid=False, reason="no evidence attached")
            )
            continue

        any_confirmed = False
        any_failed = False
        reasons: list[str] = []
        for ev in fact.evidence:
            valid, reason = reverify_evidence(ev, repo_root)
            reasons.append(reason)
            if valid is True:
                any_confirmed = True
            elif valid is False:
                any_failed = True

        still_valid = any_confirmed or not any_failed  # unverifiable-only evidence is neutral, not a failure
        results.append(
            ReverificationResult(fact_id=fact.id, subject=fact.subject, still_valid=still_valid, reason="; ".join(reasons))
        )

        updates: dict = {"last_verified": datetime.now(timezone.utc)}
        if not still_valid:
            updates["status"] = FactStatus.DISPUTED
        write_fact(fact.model_copy(update=updates), chart_dir)

    if facts:
        write_index(read_all_facts(chart_dir), chart_dir, title="The Chart")

    return results


def main() -> None:
    """CLI entrypoint: `python -m atlas.weathering <chart_dir> <repo_root>`.
    Intended to be run on a schedule (see .github/workflows/weathering.yml)
    against a real Chart directory and a checkout of the repo its evidence
    references."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Re-verify a Chart's evidence and flag stale facts.")
    parser.add_argument("chart_dir", type=Path, help="Directory containing the Chart's fact files.")
    parser.add_argument("repo_root", type=Path, help="Checkout of the repo the evidence references.")
    args = parser.parse_args()

    results = reverify_chart(args.chart_dir, args.repo_root)
    if not results:
        print(f"No facts found in {args.chart_dir} — nothing to weather.")
        return

    stale = [r for r in results if not r.still_valid]
    for r in results:
        status = "OK" if r.still_valid else "STALE"
        print(f"[{status}] {r.subject} ({r.fact_id}): {r.reason}")
    print(f"\n{len(results)} fact(s) checked, {len(stale)} newly disputed.")
    if stale:
        sys.exit(1)  # non-zero exit so a CI job surfaces this as a failure worth looking at


if __name__ == "__main__":
    main()
