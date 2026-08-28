from pathlib import Path

from atlas.ask import ask
from atlas.models import Fact
from atlas.storage import write_fact
from tests.fakes import FakeBackend


def test_ask_includes_charted_facts_in_prompt(tmp_path: Path):
    fact = Fact(subject="db_engine", scope="repo:a", claim="Uses Postgres because of JSONB columns.")
    write_fact(fact, tmp_path)

    fake = FakeBackend(response_text=f'{{"answer": "Postgres.", "cited_fact_ids": ["{fact.id}"]}}')
    result = ask("what database does this use?", tmp_path, backend=fake)

    assert result["answer"] == "Postgres."
    assert result["cited_fact_ids"] == [fact.id]
    assert fact.id in fake.calls[0][1]
    assert "what database does this use?" in fake.calls[0][1]


def test_ask_with_no_facts_still_returns_structured_response(tmp_path: Path):
    fake = FakeBackend(response_text='{"answer": "No facts are charted for this yet.", "cited_fact_ids": []}')
    result = ask("anything?", tmp_path, backend=fake)
    assert result["cited_fact_ids"] == []
    assert "No facts" in result["answer"]
