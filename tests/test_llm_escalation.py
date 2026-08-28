from atlas.cartographer.deterministic import CheckResult
from atlas.cartographer.llm_escalation import escalate_to_llm
from atlas.models import Fact
from tests.fakes import FakeBackend


def _fact(claim: str) -> Fact:
    return Fact(subject="module:auth", scope="repo:a", claim=claim)


def test_escalate_reports_conflict():
    fake = FakeBackend(response_text='{"conflict": true, "reason": "mutually exclusive states"}')
    verdict = escalate_to_llm(_fact("Uses JWT."), _fact("Uses session cookies."), backend=fake)
    assert verdict.result == CheckResult.LIKELY_CONFLICT
    assert "mutually exclusive" in verdict.reason


def test_escalate_reports_no_conflict():
    fake = FakeBackend(response_text='{"conflict": false, "reason": "both can be true, JWT was added later"}')
    verdict = escalate_to_llm(_fact("Also supports JWT."), _fact("Uses session cookies."), backend=fake)
    assert verdict.result == CheckResult.NO_CONFLICT
