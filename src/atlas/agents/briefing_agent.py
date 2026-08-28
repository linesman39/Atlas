"""The Briefing Agent (docs/project-definition.md, docs/requirements.md #4).

Compresses a Chart and/or the Atlas — never raw Field Notes — into an
Expedition Briefing sized for whoever resumes next. A human needs a
readable narrative; a fresh agent needs structured injection. Both are
real requirements; this module's LLM-backed implementation is not yet
wired up for the same reason as field_agent.py — no live SDK connection
in this repository yet.
"""

from __future__ import annotations

from atlas.models import Fact


def draft_briefing_for_human(facts: list[Fact]) -> str:
    """A readable narrative Expedition Briefing for a person resuming
    this work."""
    raise NotImplementedError("Requires a live Claude Agent SDK connection. See docs/architecture.md.")


def draft_briefing_for_agent(facts: list[Fact]) -> str:
    """A structured Expedition Briefing sized for injection into a fresh
    agent's context."""
    raise NotImplementedError("Requires a live Claude Agent SDK connection. See docs/architecture.md.")
