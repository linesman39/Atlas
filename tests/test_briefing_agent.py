from atlas.agents.briefing_agent import draft_briefing_for_agent, draft_briefing_for_human
from atlas.models import Fact
from tests.fakes import FakeBackend


def test_draft_briefing_for_human_returns_backend_text():
    fake = FakeBackend(response_text="Session storage moved from Redis to Postgres. Nothing else open.")
    facts = [Fact(subject="module:session_store", scope="repo:payments-api", claim="Uses Postgres.")]
    briefing = draft_briefing_for_human(facts, backend=fake)
    assert briefing == "Session storage moved from Redis to Postgres. Nothing else open."
    assert "module:session_store" in fake.calls[0][1]


def test_draft_briefing_for_agent_uses_agent_prompt():
    fake = FakeBackend(response_text="- constraint: ...")
    facts = [Fact(subject="module:session_store", scope="repo:payments-api", claim="Uses Postgres.")]
    draft_briefing_for_agent(facts, backend=fake)
    assert "fresh coding agent" in fake.calls[0][0]
