"""The LLM layer: pluggable backends behind one interface (base.LLMBackend).

Engine vs. Application, applied to inference: the default backend is
`OllamaBackend` — free, local, no account, no key, same story as git
needing no service to function. `ClaudeBackend` is the optional
"GitHub" of this layer: better-resourced, hosted, opt-in, never assumed.
See docs/architecture.md, "Engine vs. Application".

Select with the ATLAS_LLM_BACKEND environment variable: "local" (default)
or "claude". Never silently reach for a paid backend.
"""

from __future__ import annotations

import os

from atlas.llm.base import LLMBackend, LLMCallResult, extract_json

__all__ = ["LLMBackend", "LLMCallResult", "extract_json", "get_default_backend"]

_cached_default: LLMBackend | None = None


def get_default_backend() -> LLMBackend:
    global _cached_default
    if _cached_default is not None:
        return _cached_default

    choice = os.environ.get("ATLAS_LLM_BACKEND", "local").lower()
    if choice == "local":
        from atlas.llm.local import OllamaBackend

        _cached_default = OllamaBackend(model=os.environ.get("ATLAS_LLM_MODEL", "llama3.1"))
    elif choice == "claude":
        from atlas.llm.claude import ClaudeBackend

        _cached_default = ClaudeBackend()
    else:
        raise ValueError(f"Unknown ATLAS_LLM_BACKEND={choice!r}. Use 'local' or 'claude'.")
    return _cached_default
