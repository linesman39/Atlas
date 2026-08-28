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
from atlas.codeowners import owners_for_fact, parse_codeowners
from atlas.models import AnnexationRequest, AnnexationVerdict, Fact
from atlas.storage import fact_to_markdown, read_all_facts

_CODEOWNERS_PATHS = ("CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS")


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


def format_trade_route_pr_title(fact: Fact) -> str:
    return f"Trade route: {fact.subject}"


def format_trade_route_pr_body(fact: Fact) -> str:
    """Pure function: the PR body a receiving org's Surveyor-General
    reviews. A trade-route PR is annexation with a wider audience, not a
    different mechanism (docs/architecture.md, "Trade routes") — so it
    carries the same evidence and confidence a normal annexation would."""
    lines = [
        "Proposed via a trade route from another Atlas workspace — a fact "
        "explicitly marked shareable, exported the same way any annexation "
        "would be reviewed here.",
        "",
        f"**Subject**: `{fact.subject}`  ",
        f"**Original scope**: `{fact.scope}`  ",
        f"**Confidence**: {fact.confidence:.2f}",
        "",
        "## Claim",
        fact.claim,
        "",
        "## Evidence",
    ]
    if not fact.evidence:
        lines.append("_None attached._")
    else:
        for ev in fact.evidence:
            lines.append(f"- **{ev.kind.value}**: `{ev.reference}` — {ev.summary}".rstrip(" —"))
    return "\n".join(lines) + "\n"


class GitHubAdapter(SubstrateAdapter):
    """Charts and the Atlas live as directories of fact files inside a
    GitHub repository; annexation is a branch + PR against that repo."""

    def __init__(self, token: str, repo_full_name: str, facts_dir: str = "facts"):
        try:
            from github import Github
        except ImportError as exc:
            raise ImportError(
                "GitHubAdapter requires the optional 'github' extra: pip install 'atlas-cartographer[github]'. "
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
        self._request_codeowners_review(pr, request.fact)
        return AnnexationHandle(url=pr.html_url, is_open=True)

    def _request_codeowners_review(self, pr, fact: Fact) -> None:
        """Route the annexation PR to the accountable Surveyor-General via
        CODEOWNERS, reusing GitHub's own reviewer-assignment API instead
        of a bespoke routing system (docs/architecture.md, "Committed
        beyond the original core"). Silently does nothing if the repo has
        no CODEOWNERS file or the owners it names aren't valid
        reviewers — a missing or partial CODEOWNERS setup should never
        block the annexation itself, only skip the convenience of
        auto-routing it."""
        from github.GithubException import UnknownObjectException

        content = None
        for path in _CODEOWNERS_PATHS:
            try:
                content = self._repo.get_contents(path).decoded_content.decode("utf-8")
                break
            except UnknownObjectException:
                continue
        if content is None:
            return

        rules = parse_codeowners(content)
        owners = owners_for_fact(rules, fact.subject, facts_dir=self._facts_dir)
        if not owners:
            return

        individuals = [o.lstrip("@") for o in owners if "/" not in o]
        teams = [o.lstrip("@").split("/", 1)[1] for o in owners if "/" in o]
        try:
            if individuals or teams:
                pr.create_review_request(reviewers=individuals or None, team_reviewers=teams or None)
        except Exception:
            # A named owner might not actually have push access to this
            # repo, or a team slug might not resolve -- routing is a
            # convenience layered on top of a real, already-open PR, not
            # something that should make annexation itself fail.
            pass

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

    def propose_trade_route(self, fact: Fact, target_repo_full_name: str) -> AnnexationHandle:
        """Export a shareable fact as a fork-and-PR into another
        workspace's Atlas repository — reusing GitHub's existing
        cross-org contribution model (fork, branch, PR) instead of a
        bespoke sharing protocol. See docs/architecture.md, "Trade routes"."""
        if not fact.shareable:
            raise ValueError(f"Fact {fact.id} is not marked shareable — cannot open a trade route for it.")

        target_repo = self._client.get_repo(target_repo_full_name)
        fork = self._client.get_user().create_fork(target_repo)
        branch_name = f"trade-route/{fact.id}"
        default_branch = target_repo.default_branch
        base_sha = fork.get_branch(default_branch).commit.sha
        fork.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_sha)

        path = f"{self._facts_dir}/{fact.subject.lower().replace(' ', '-')}-{fact.id}.md"
        fork.create_file(
            path=path,
            message=format_trade_route_pr_title(fact),
            content=fact_to_markdown(fact),
            branch=branch_name,
        )

        pr = target_repo.create_pull(
            title=format_trade_route_pr_title(fact),
            body=format_trade_route_pr_body(fact),
            head=f"{fork.owner.login}:{branch_name}",
            base=default_branch,
        )
        return AnnexationHandle(url=pr.html_url, is_open=True)
