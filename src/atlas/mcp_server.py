"""Atlas's MCP integration surface (docs/architecture.md, "The
Application").

Exposes the engine to any MCP client — Claude Code today, in principle
anything MCP-speaking tomorrow — as four tools. This module is a client
of the engine, same discipline as the GitHub adapter and the
visualization layer: nothing here is a second source of truth, it reads
and writes the same Chart/Atlas files atlas.storage already defines.

Run standalone: `python -m atlas.mcp_server` (stdio transport, for a
local MCP client config to point at).
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.mcpserver import MCPServer

from atlas.agents.briefing_agent import draft_briefing_for_agent, draft_briefing_for_human
from atlas.agents.field_agent import extract_field_notes
from atlas.local_annex import annex_locally
from atlas.models import EvidenceKind, EvidenceRef, Fact, Tier
from atlas.storage import read_all_facts

server = MCPServer(
    name="atlas",
    instructions=(
        "Atlas: ground-truthed, cross-repository memory for coding-agent sessions. "
        "Use record_field_note to log what happened in a session, propose_annexation to "
        "promote a ground-truthed fact into a Chart, query_chart to read what's already "
        "known, and get_briefing to bootstrap a fresh session or hand off to a human."
    ),
)


@server.tool()
def record_field_note(session_id: str, transcript_segment: str) -> list[dict]:
    """Extract structured Field Notes (decisions, constraints, rejected approaches,
    open questions) from a segment of a coding session transcript."""
    notes = extract_field_notes(session_id, transcript_segment)
    return [n.model_dump(mode="json") for n in notes]


@server.tool()
def propose_annexation(
    chart_dir: str,
    subject: str,
    scope: str,
    claim: str,
    evidence_reference: str,
    evidence_summary: str,
    value: str | None = None,
    evidence_kind: str = "diff",
    tier: str = "chart",
) -> dict:
    """Propose a ground-truthed fact for annexation into the Chart at
    chart_dir. Requires real evidence (a test result, diff, or command
    output) — a fact with none is rejected before any conflict check
    even runs. Returns the Cartographer's verdict; only an APPROVED
    verdict actually writes anything."""
    candidate = Fact(
        subject=subject,
        scope=scope,
        claim=claim,
        value=value,
        tier=Tier(tier),
        evidence=[EvidenceRef(kind=EvidenceKind(evidence_kind), reference=evidence_reference, summary=evidence_summary)],
    )
    decision = annex_locally(candidate, Path(chart_dir))
    return decision.model_dump(mode="json")


@server.tool()
def query_chart(chart_dir: str) -> list[dict]:
    """Read every currently-annexed fact from the Chart at chart_dir."""
    facts = read_all_facts(Path(chart_dir))
    return [f.model_dump(mode="json") for f in facts]


@server.tool()
def get_briefing(chart_dir: str, audience: str = "human") -> str:
    """Draft an Expedition Briefing from the Chart at chart_dir.
    audience: "human" for a readable narrative, "agent" for terse
    structured bullets sized for a fresh agent's context."""
    facts = read_all_facts(Path(chart_dir))
    if audience == "agent":
        return draft_briefing_for_agent(facts)
    return draft_briefing_for_human(facts)


if __name__ == "__main__":
    server.run()
