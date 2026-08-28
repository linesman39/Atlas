"""The optional hosted backend — Claude via the Agent SDK, for a user who
wants higher-quality extraction/judgment than their local model gives and
is willing to pay for it. This is the "GitHub" of the LLM layer: an
optional, better-resourced service built on top of a free engine that
works without it. Never the default — see atlas.llm.get_default_backend().

Cost finding worth keeping on record: the SDK's default configuration
loads this environment's full skill/command/system-prompt set on every
call — about $0.09 and ~22k cache-creation tokens overhead for a one-word
reply. Disabling `setting_sources`, `skills`, and default `tools`, and
supplying a narrow system prompt, cuts that to ~$0.002 with no functional
loss for a narrow extraction/judgment task.
"""

from __future__ import annotations

import asyncio

from atlas.llm.base import LLMBackend, LLMCallResult


class ClaudeBackend(LLMBackend):
    def __init__(self, max_budget_usd: float = 0.20):
        try:
            import claude_agent_sdk  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "ClaudeBackend requires the optional 'claude' extra: pip install 'atlas-map[claude]'. "
                "The engine works without it — see docs/architecture.md, 'Engine vs. Application'."
            ) from exc
        self.max_budget_usd = max_budget_usd

    def complete(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        return asyncio.run(self._complete_async(system_prompt, user_prompt))

    async def _complete_async(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

        opts = ClaudeAgentOptions(
            max_turns=1,
            setting_sources=[],
            skills=None,
            tools=[],
            system_prompt=system_prompt,
            max_budget_usd=self.max_budget_usd,
        )
        text_parts: list[str] = []
        cost = 0.0
        input_tokens = 0
        output_tokens = 0
        async for msg in query(prompt=user_prompt, options=opts):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        text_parts.append(block.text)
            elif isinstance(msg, ResultMessage):
                cost = msg.total_cost_usd or 0.0
                input_tokens = msg.usage.get("input_tokens", 0)
                output_tokens = msg.usage.get("output_tokens", 0)
        return LLMCallResult(
            text="".join(text_parts), cost_usd=cost, input_tokens=input_tokens, output_tokens=output_tokens
        )
