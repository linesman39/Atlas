"""Tests atlas.llm.get_default_backend -- the actual selection logic
behind the project's central guarantee (free/local by default, hosted
only on explicit opt-in). Previously untested (0% coverage on this
branch, found via `pytest --cov`); this closes that gap.

Resets the module-level cache before/after each test since
get_default_backend() memoizes into a process-global."""

import importlib

import pytest

import atlas.llm as atlas_llm
from atlas.llm.local import OllamaBackend


@pytest.fixture(autouse=True)
def _reset_cache(monkeypatch):
    atlas_llm._cached_default = None
    yield
    atlas_llm._cached_default = None


def test_defaults_to_local_when_env_var_unset(monkeypatch):
    monkeypatch.delenv("ATLAS_LLM_BACKEND", raising=False)
    backend = atlas_llm.get_default_backend()
    assert isinstance(backend, OllamaBackend)
    assert backend.model == "llama3.1"


def test_explicit_local_selection(monkeypatch):
    monkeypatch.setenv("ATLAS_LLM_BACKEND", "local")
    backend = atlas_llm.get_default_backend()
    assert isinstance(backend, OllamaBackend)


def test_local_model_override_respected(monkeypatch):
    monkeypatch.setenv("ATLAS_LLM_BACKEND", "local")
    monkeypatch.setenv("ATLAS_LLM_MODEL", "mistral")
    backend = atlas_llm.get_default_backend()
    assert backend.model == "mistral"


def test_selection_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("ATLAS_LLM_BACKEND", "LOCAL")
    backend = atlas_llm.get_default_backend()
    assert isinstance(backend, OllamaBackend)


def test_result_is_cached_across_calls(monkeypatch):
    monkeypatch.delenv("ATLAS_LLM_BACKEND", raising=False)
    first = atlas_llm.get_default_backend()
    second = atlas_llm.get_default_backend()
    assert first is second


def test_unknown_backend_raises_value_error(monkeypatch):
    monkeypatch.setenv("ATLAS_LLM_BACKEND", "not-a-real-backend")
    with pytest.raises(ValueError, match="Unknown ATLAS_LLM_BACKEND"):
        atlas_llm.get_default_backend()


def test_claude_selection_matches_environment_reality(monkeypatch):
    """If claude-agent-sdk is installed (the [claude] extra), selecting it
    must succeed. If it isn't (the base engine install, and CI's default
    profile), it must fail with the documented ImportError -- never
    silently fall back to something else."""
    monkeypatch.setenv("ATLAS_LLM_BACKEND", "claude")
    try:
        importlib.import_module("claude_agent_sdk")
        sdk_installed = True
    except ImportError:
        sdk_installed = False

    if sdk_installed:
        from atlas.llm.claude import ClaudeBackend

        backend = atlas_llm.get_default_backend()
        assert isinstance(backend, ClaudeBackend)
    else:
        with pytest.raises(ImportError, match="claude"):
            atlas_llm.get_default_backend()
