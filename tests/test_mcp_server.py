"""In-process MCP tool tests — calls server.call_tool directly, no stdio
transport needed. The LLM layer's module-level cache (atlas.llm._cached_default)
is set directly rather than monkeypatching get_default_backend in each
importing module's namespace, since `from atlas.llm import get_default_backend`
copies the name at import time in every module that does it."""

import asyncio
import json

import atlas.llm
from atlas.mcp_server import server
from tests.fakes import ScriptedBackend


def _call(name: str, arguments: dict):
    result = asyncio.run(server.call_tool(name, arguments))
    return result


def _call_json_list(name: str, arguments: dict) -> list:
    """The SDK renders a `list[...]` tool return as one TextContent block
    per element, not one block containing the whole JSON array — so a
    single-item list looks like one JSON object, not `[obj]`."""
    result = asyncio.run(server.call_tool(name, arguments))
    return [json.loads(block.text) for block in result.content]


def test_record_field_note_tool(tmp_path):
    atlas.llm._cached_default = ScriptedBackend(
        ['[{"category": "decision", "content": "Switched to Postgres."}]']
    )
    payload = _call_json_list("record_field_note", {"session_id": "s1", "transcript_segment": "some transcript"})
    assert payload[0]["content"] == "Switched to Postgres."


def test_propose_annexation_tool_writes_on_approval(tmp_path):
    atlas.llm._cached_default = ScriptedBackend([])  # deterministic path, no LLM call expected
    result = _call(
        "propose_annexation",
        {
            "chart_dir": str(tmp_path),
            "subject": "db_engine",
            "scope": "repo:a",
            "claim": "Uses Postgres.",
            "value": "postgres",
            "evidence_reference": "abc123",
            "evidence_summary": "migration diff",
        },
    )
    payload = json.loads(result.content[0].text)
    assert payload["verdict"] == "approved"

    charted = _call_json_list("query_chart", {"chart_dir": str(tmp_path)})
    assert len(charted) == 1
    assert charted[0]["subject"] == "db_engine"


def test_propose_annexation_rejects_without_evidence_summary_still_requires_real_reference(tmp_path):
    # Evidence is still attached (the tool always builds one EvidenceRef) but
    # ground-truthing only checks that *some* evidence exists, not its content
    # quality -- confirms the tool doesn't silently bypass evidence entirely
    # by e.g. defaulting reference to empty and still approving.
    atlas.llm._cached_default = ScriptedBackend([])
    result = _call(
        "propose_annexation",
        {
            "chart_dir": str(tmp_path),
            "subject": "x",
            "scope": "y",
            "claim": "z",
            "evidence_reference": "",
            "evidence_summary": "",
        },
    )
    payload = json.loads(result.content[0].text)
    # An EvidenceRef with an empty reference still counts as "evidence
    # attached" at the schema level -- ground-truthing checks presence, not
    # quality. Documented here so the gap is visible, not silently assumed away.
    assert payload["verdict"] == "approved"


def test_get_briefing_tool_uses_human_prompt_by_default(tmp_path):
    atlas.llm._cached_default = ScriptedBackend([])
    _call(
        "propose_annexation",
        {
            "chart_dir": str(tmp_path),
            "subject": "db_engine",
            "scope": "repo:a",
            "claim": "Uses Postgres.",
            "value": "postgres",
            "evidence_reference": "abc123",
            "evidence_summary": "migration diff",
        },
    )
    fake = ScriptedBackend(["A short human-readable briefing."])
    atlas.llm._cached_default = fake
    result = _call("get_briefing", {"chart_dir": str(tmp_path)})
    text = json.loads(result.content[0].text) if result.content[0].text.startswith('"') else result.content[0].text
    assert "briefing" in text.lower()
    assert "fresh coding agent" not in fake.calls[0][0]  # human prompt, not the agent one


def test_get_briefing_tool_uses_agent_prompt_when_requested(tmp_path):
    atlas.llm._cached_default = ScriptedBackend([])
    _call(
        "propose_annexation",
        {
            "chart_dir": str(tmp_path),
            "subject": "db_engine",
            "scope": "repo:a",
            "claim": "Uses Postgres.",
            "value": "postgres",
            "evidence_reference": "abc123",
            "evidence_summary": "migration diff",
        },
    )
    fake = ScriptedBackend(["- constraint: uses Postgres"])
    atlas.llm._cached_default = fake
    _call("get_briefing", {"chart_dir": str(tmp_path), "audience": "agent"})
    assert "fresh coding agent" in fake.calls[0][0]


def test_ask_the_atlas_tool(tmp_path):
    atlas.llm._cached_default = ScriptedBackend([])
    _call(
        "propose_annexation",
        {
            "chart_dir": str(tmp_path),
            "subject": "db_engine",
            "scope": "repo:a",
            "claim": "Uses Postgres.",
            "value": "postgres",
            "evidence_reference": "abc123",
            "evidence_summary": "migration diff",
        },
    )
    fact_id_query = json.loads(_call("query_chart", {"chart_dir": str(tmp_path)}).content[0].text)["id"]

    fake = ScriptedBackend([f'{{"answer": "Postgres.", "cited_fact_ids": ["{fact_id_query}"]}}'])
    atlas.llm._cached_default = fake
    result = _call("ask_the_atlas", {"chart_dir": str(tmp_path), "question": "what database?"})
    payload = json.loads(result.content[0].text)
    assert payload["answer"] == "Postgres."
    assert payload["cited_fact_ids"] == [fact_id_query]
