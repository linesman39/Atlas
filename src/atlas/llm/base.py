"""The LLM backend boundary — the same adapter discipline applied to
model inference that adapters/base.py applies to hosting (docs/architecture.md).

Nothing in atlas.agents or atlas.cartographer may import a specific
backend directly. They call whatever LLMBackend they're given (or the
default one), so the engine never assumes a paid API is available.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMCallResult:
    text: str
    cost_usd: float
    input_tokens: int
    output_tokens: int


class LLMBackend(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        """Run one single-turn completion. Implementations should be
        deterministic about cost accounting: a truly local backend
        reports cost_usd=0.0, never an estimate."""


def extract_json(text: str) -> Any:
    """Models wrap JSON in prose or code fences surprisingly often even
    when told not to — local, smaller models more than most. Pull out
    the first balanced {...} or [...] block. Backend-agnostic on purpose."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    for i, ch in enumerate(text):
        if ch in "{[":
            open_ch, close_ch = ch, ("}" if ch == "{" else "]")
            depth = 0
            for j in range(i, len(text)):
                if text[j] == open_ch:
                    depth += 1
                elif text[j] == close_ch:
                    depth -= 1
                    if depth == 0:
                        return json.loads(text[i : j + 1])
    raise ValueError(f"No JSON object/array found in LLM output: {text!r}")
