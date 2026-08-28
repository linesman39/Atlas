"""GitHub as the first substrate adapter (docs/architecture.md).

Annexation-as-pull-request: a candidate fact becomes a real, diffable,
commentable GitHub PR, reviewed by a Surveyor-General through the normal
review flow a team already has. This module is the only place in Atlas
that imports PyGithub or knows GitHub's API exists — see adapters/base.py.

Note: the PR-formatting logic below is pure and unit-tested
(tests/test_github_adapter.py). The live API calls (branch creation, PR
open, review-state check) are real, ordinary PyGithub usage but are not
exercised against a live repository as part of this codebase's own test
suite, to avoid a test run silently opening real PRs against whatever
GITHUB_TOKEN happens to be in the environment.
"""

from __future__ import annotations

from atlas.adapters.base import AnnexationHandle, SubstrateAdapter
from atlas.models import AnnexationRequest, AnnexationVerdict, Fact
from atlas.storage import fact_to_markdown, read_all_facts


def format_annexation_pr_title(request: AnnexationRequest) -> str:
    return f"Annex: {request.fact.subject} ({request.target_tier.value})"


def format_annexation_pr_body(request: AnnexationRequest) -> str:
    """Pure function: the PR body a Surveyor-General reviews. Must show
    the fact, its evidence, and the Cartographer's verdict — a reviewer
    should never have to leave the PR to judge this."""
    fact = request.fact
    lines = [
        f"**Subject**: `{fact.subject}`  ",
        f"**Scope**: `{fact.scope}`  ",
        f"**Target tier**: `{request.target_tier.value}`  ",
        f"**Confidence**: {fact.confidence:.2f}",
        "",
        "## Claim",
        fact.claim,
        "",
        "## Evidence",
    ]
    if not fact.evidence:
        lines.append("_None attached — this annexation should not have been proposed without evidence._")
    else:
        for ev in fact.evidence:
            lines.append(f"- **{ev.kind.value}**: `{ev.reference}` — {ev.summary}".rstrip(" —"))

    lines += ["", "## Cartographer verdict"]
    if request.verdict == AnnexationVerdict.APPROVED:
        lines.append("✅ No border dispute detected.")
    elif request.verdict == AnnexationVerdict.DISPUTED and request.dispute:
        lines += [
            "⚠️ **Border dispute** — this fact conflicts with an existing one.",
            f"- Conflicts with fact `{request.dispute.existing_fact_id}`",
            f"- Reason: {request.dispute.reason}",
            f"- Detected by: {request.dispute.detected_by}",
        ]
    else:
        lines.append(f"`{request.verdict.value if request.verdict else 'pending'}`")

    return "\n".join(lines) + "\n"


class GitHubAdapter(SubstrateAdapter):
    """Charts and the Atlas live as directories of fact files inside a
    GitHub repository; annexation is a branch + PR against that repo."""

    def __init__(self, token: str, repo_full_name: str, facts_dir: str = "facts"):
        try:
            from github import Github
        except ImportError as exc:
            raise ImportError(
                "GitHubAdapter requires the optional 'github' extra: pip install 'atlas-map[github]'. "
                "The engine works without it — see docs/architecture.md, 'Engine vs. Application'."
            ) from exc
        self._client = Github(token)
        self._repo = self._client.get_repo(repo_full_name)
        self._facts_dir = facts_dir

    def propose_annexation(self, request: AnnexationRequest) -> AnnexationHandle:
        branch_name = f"annex/{request.fact.id}"
        default_branch = self._repo.default_branch
        base_sha = self._repo.get_branch(default_branch).commit.sha
        self._repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_sha)

        path = f"{self._facts_dir}/{request.fact.subject.lower().replace(' ', '-')}-{request.fact.id}.md"
        content = fact_to_markdown(request.fact)
        self._repo.create_file(
            path=path,
            message=format_annexation_pr_title(request),
            content=content,
            branch=branch_name,
        )

        pr = self._repo.create_pull(
            title=format_annexation_pr_title(request),
            body=format_annexation_pr_body(request),
            head=branch_name,
            base=default_branch,
        )
        return AnnexationHandle(url=pr.html_url, is_open=True)

    def is_approved(self, handle: AnnexationHandle) -> bool:
        pr_number = int(handle.url.rstrip("/").rsplit("/", 1)[-1])
        pr = self._repo.get_pull(pr_number)
        reviews = pr.get_reviews()
        return any(r.state == "APPROVED" for r in reviews) and pr.merged

    def get_facts(self, scope: str) -> list[Fact]:
        # Real repos read this from a local clone kept in sync with the
        # substrate; for the adapter's own contract, callers pass a local
        # checkout path via `scope` in this minimal implementation.
        from pathlib import Path

        return read_all_facts(Path(scope) / self._facts_dir)
