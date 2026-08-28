from unittest.mock import MagicMock

import pytest
from github.GithubException import UnknownObjectException

from atlas.adapters.github import (
    GitHubAdapter,
    format_annexation_pr_body,
    format_annexation_pr_title,
    format_trade_route_pr_body,
    format_trade_route_pr_title,
)
from atlas.models import AnnexationRequest, AnnexationVerdict, BorderDispute, EvidenceKind, EvidenceRef, Fact, Tier


def _grounded_fact() -> Fact:
    return Fact(
        subject="library:redis",
        scope="repo:payments-api",
        claim="Do not use Redis for session storage.",
        evidence=[EvidenceRef(kind=EvidenceKind.TEST_RESULT, reference="tests/test_load.py", summary="dropped sessions under load")],
    )


def test_pr_title_includes_subject_and_tier():
    request = AnnexationRequest(fact=_grounded_fact(), target_tier=Tier.CHART, verdict=AnnexationVerdict.APPROVED)
    title = format_annexation_pr_title(request)
    assert "library:redis" in title
    assert "chart" in title


def test_pr_body_shows_evidence():
    request = AnnexationRequest(fact=_grounded_fact(), target_tier=Tier.CHART, verdict=AnnexationVerdict.APPROVED)
    body = format_annexation_pr_body(request)
    assert "tests/test_load.py" in body
    assert "No border dispute" in body


def test_pr_body_flags_missing_evidence():
    ungrounded = Fact(subject="library:foo", scope="global", claim="Some claim with no evidence.")
    request = AnnexationRequest(fact=ungrounded, target_tier=Tier.CHART, verdict=AnnexationVerdict.APPROVED)
    body = format_annexation_pr_body(request)
    assert "should not have been proposed without evidence" in body


def test_pr_body_shows_border_dispute():
    dispute = BorderDispute(
        existing_fact_id="abc123",
        candidate_fact_id="def456",
        reason="Contradicts existing fact: postgres -> redis for the same subject/scope.",
        detected_by="deterministic",
    )
    request = AnnexationRequest(
        fact=_grounded_fact(),
        target_tier=Tier.CHART,
        verdict=AnnexationVerdict.DISPUTED,
        dispute=dispute,
    )
    body = format_annexation_pr_body(request)
    assert "Border dispute" in body
    assert "abc123" in body


def test_trade_route_pr_title_and_body():
    fact = _grounded_fact()
    assert fact.subject in format_trade_route_pr_title(fact)

    body = format_trade_route_pr_body(fact)
    assert "trade route from another Atlas workspace" in body
    assert fact.scope in body
    assert "tests/test_load.py" in body


def test_propose_trade_route_refuses_unshareable_fact():
    fact = _grounded_fact()
    assert fact.shareable is False
    adapter = GitHubAdapter.__new__(GitHubAdapter)  # skip __init__, no real token/repo needed for this guard
    with pytest.raises(ValueError, match="not marked shareable"):
        adapter.propose_trade_route(fact, "some-org/some-repo")


def _bare_adapter(repo, facts_dir: str = "facts") -> GitHubAdapter:
    adapter = GitHubAdapter.__new__(GitHubAdapter)
    adapter._client = MagicMock()
    adapter._repo = repo
    adapter._facts_dir = facts_dir
    return adapter


def test_codeowners_review_requested_when_owner_found():
    repo = MagicMock()
    repo.get_contents.return_value.decoded_content = b"/facts/library:redis* @my-org/security-team\n"
    pr = MagicMock()

    adapter = _bare_adapter(repo)
    adapter._request_codeowners_review(pr, _grounded_fact())

    pr.create_review_request.assert_called_once_with(reviewers=None, team_reviewers=["security-team"])


def test_codeowners_review_skipped_when_no_codeowners_file():
    repo = MagicMock()
    repo.get_contents.side_effect = UnknownObjectException(404, "not found", None)
    pr = MagicMock()

    adapter = _bare_adapter(repo)
    adapter._request_codeowners_review(pr, _grounded_fact())  # must not raise

    pr.create_review_request.assert_not_called()


def test_codeowners_review_skipped_when_no_owner_matches():
    repo = MagicMock()
    repo.get_contents.return_value.decoded_content = b"/facts/billing-* @billing-team\n"
    pr = MagicMock()

    adapter = _bare_adapter(repo)
    adapter._request_codeowners_review(pr, _grounded_fact())  # subject is library:redis, no match

    pr.create_review_request.assert_not_called()


def test_codeowners_review_requests_individual_reviewer():
    repo = MagicMock()
    repo.get_contents.return_value.decoded_content = b"/facts/library:redis* @alice\n"
    pr = MagicMock()

    adapter = _bare_adapter(repo)
    adapter._request_codeowners_review(pr, _grounded_fact())

    pr.create_review_request.assert_called_once_with(reviewers=["alice"], team_reviewers=None)


def test_codeowners_review_failure_does_not_raise():
    repo = MagicMock()
    repo.get_contents.return_value.decoded_content = b"/facts/library:redis* @my-org/security-team\n"
    pr = MagicMock()
    pr.create_review_request.side_effect = RuntimeError("not a valid reviewer")

    adapter = _bare_adapter(repo)
    adapter._request_codeowners_review(pr, _grounded_fact())  # must swallow the error, not propagate
