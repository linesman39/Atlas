"""The Briefing Agent (docs/project-definition.md, docs/requirements.md #4).

Compresses a Chart and/or the Atlas — never raw Field Notes — into an
Expedition Briefing sized for whoever resumes next. A human needs a
readable narrative; a fresh agent needs terse structured injection —
these are genuinely different outputs, not the same text at two lengths.

Runs against whatever LLMBackend it's given, defaulting to the engine's
free local backend.
"""

from __future__ import annotations

from atlas.llm import LLMBackend, get_default_backend
from atlas.models import Fact

_HUMAN_SYSTEM_PROMPT = """You are the Briefing Agent in the Atlas project. Write a short, plain-English Expedition Briefing for a human picking up this work, from the list of charted facts given. Group related facts, note what's still open or disputed, and keep it under 200 words. No preamble — write only the briefing itself."""

_AGENT_SYSTEM_PROMPT = """You are the Briefing Agent in the Atlas project. Write a compact, structured Expedition Briefing for a fresh coding agent about to start work, from the list of charted facts given. Use terse bullet points grouped by category: constraints, decisions, rejected approaches, open questions. No preamble — write only the briefing itself."""


def _facts_block(facts: list[Fact]) -> str:
    return "\n".join(f"- [{f.subject} / {f.scope}] {f.claim}" for f in facts)


def draft_briefing_for_human(facts: list[Fact], backend: LLMBackend | None = None) -> str:
    backend = backend or get_default_backend()
    result = backend.complete(_HUMAN_SYSTEM_PROMPT, _facts_block(facts))
    return result.text


def draft_briefing_for_agent(facts: list[Fact], backend: LLMBackend | None = None) -> str:
    backend = backend or get_default_backend()
    result = backend.complete(_AGENT_SYSTEM_PROMPT, _facts_block(facts))
    return result.text
