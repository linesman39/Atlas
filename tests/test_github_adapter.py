import pytest

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
