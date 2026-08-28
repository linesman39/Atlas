"""Ask-the-Atlas: a query tool, not a second source of truth. Every
answer must cite the facts it came from — ground-truthing enforced at
query time the same way it's enforced at write time (docs/architecture.md,
"Committed beyond today's build").
"""

from __future__ import annotations

from pathlib import Path

from atlas.llm import LLMBackend, extract_json, get_default_backend
from atlas.models import Fact
from atlas.storage import read_all_facts

_SYSTEM_PROMPT = """You are Ask-the-Atlas. Answer the question using ONLY the facts given — never information you already know from training. If the facts don't answer the question, say so plainly rather than guessing.

Reply with ONLY JSON, no prose: {"answer": "<your answer, or a clear statement that the facts don't cover it>", "cited_fact_ids": ["<id>", ...]}

cited_fact_ids must list the id of every fact your answer actually relies on. An answer with no citation is only acceptable when you're saying the facts don't cover the question.
"""


def _facts_block(facts: list[Fact]) -> str:
    return "\n".join(f"[{f.id}] ({f.subject} / {f.scope}) {f.claim}" for f in facts)


def ask(question: str, chart_dir: Path, backend: LLMBackend | None = None) -> dict:
    backend = backend or get_default_backend()
    facts = read_all_facts(chart_dir)
    prompt = f"Facts:\n{_facts_block(facts)}\n\nQuestion: {question}"
    result = backend.complete(_SYSTEM_PROMPT, prompt)
    data = extract_json(result.text)
    return {
        "answer": data.get("answer", ""),
        "cited_fact_ids": data.get("cited_fact_ids", []),
    }
