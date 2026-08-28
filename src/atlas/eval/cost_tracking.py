"""A backend decorator that measures cost and wall-clock latency around
any wrapped LLMBackend, for the evaluation harness's per-item reporting.
Kept as a decorator (not a change to LLMBackend's own interface) so the
agents don't need to know they're being measured."""

from __future__ import annotations

import time

from atlas.llm.base import LLMBackend, LLMCallResult


class CostTrackingBackend(LLMBackend):
    def __init__(self, inner: LLMBackend):
        self.inner = inner
        self.total_cost_usd = 0.0
        self.total_latency_s = 0.0
        self.call_count = 0

    def complete(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        start = time.monotonic()
        result = self.inner.complete(system_prompt, user_prompt)
        elapsed = time.monotonic() - start
        self.total_cost_usd += result.cost_usd
        self.total_latency_s += elapsed
        self.call_count += 1
        return result
