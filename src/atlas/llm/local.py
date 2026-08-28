"""The engine's default backend: a local model via Ollama.

This is the piece that makes Atlas free like git rather than metered like
a hosted API — no key, no account, no per-call cost. Ollama was chosen
because it's the most widely adopted way to run an open model locally
behind a stable, simple HTTP API (OpenAI-chat-shaped), so a user gets a
working local backend with `ollama pull <model>` and nothing else to
configure.

Uses only the standard library (urllib) — the engine's default path
shouldn't need a third-party HTTP client dependency.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from atlas.llm.base import LLMBackend, LLMCallResult

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1"


class OllamaNotReachableError(RuntimeError):
    def __init__(self, base_url: str):
        super().__init__(
            f"Could not reach a local Ollama server at {base_url}. "
            f"Install Ollama (https://ollama.com) and run `ollama pull {DEFAULT_MODEL}`, "
            "or set ATLAS_LLM_BACKEND=claude to use a hosted model instead "
            "(see docs/architecture.md, 'Engine vs. Application')."
        )


class OllamaBackend(LLMBackend):
    """Zero-cost by construction: this backend never reports a nonzero
    cost_usd, because nothing was billed."""

    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL, timeout: float = 120.0):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, system_prompt: str, user_prompt: str) -> LLMCallResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
            raise OllamaNotReachableError(self.base_url) from exc

        text = data.get("message", {}).get("content", "")
        eval_count = data.get("eval_count", 0)
        prompt_eval_count = data.get("prompt_eval_count", 0)
        return LLMCallResult(text=text, cost_usd=0.0, input_tokens=prompt_eval_count, output_tokens=eval_count)
