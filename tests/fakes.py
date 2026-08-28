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


class ScriptedBackend(LLMBackend):
    """Returns queued responses in call order — for testing orchestration
    logic that makes several different calls in sequence."""

    def __init__(self, responses: list[str], cost_per_call: float = 0.0):
        self.responses = list(responses)
        self.cost_per_call = cost_per_call
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        self.calls.append((system_prompt, user_prompt))
        text = self.responses.pop(0)
        return LLMCallResult(text=text, cost_usd=self.cost_per_call, input_tokens=0, output_tokens=0)
