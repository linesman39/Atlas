"""A fake LLMBackend for testing agent logic without a network call —
neither Ollama nor a paid API should be required to run this test suite."""

from __future__ import annotations

from atlas.llm.base import LLMBackend, LLMCallResult


class FakeBackend(LLMBackend):
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        self.calls.append((system_prompt, user_prompt))
        return LLMCallResult(text=self.response_text, cost_usd=0.0, input_tokens=0, output_tokens=0)
