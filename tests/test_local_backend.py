import json
from unittest.mock import MagicMock, patch

import pytest

from atlas.llm.local import DEFAULT_BASE_URL, OllamaBackend, OllamaNotReachableError


def _fake_response(payload: dict):
    mock = MagicMock()
    mock.read.return_value = json.dumps(payload).encode("utf-8")
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = False
    return mock


def test_complete_parses_ollama_response():
    backend = OllamaBackend()
    fake_payload = {
        "message": {"content": "hello from a local model"},
        "prompt_eval_count": 12,
        "eval_count": 5,
    }
    with patch("urllib.request.urlopen", return_value=_fake_response(fake_payload)):
        result = backend.complete("system", "user")

    assert result.text == "hello from a local model"
    assert result.cost_usd == 0.0  # zero-cost by construction, never estimated
    assert result.input_tokens == 12
    assert result.output_tokens == 5


def test_sends_correct_request_shape():
    backend = OllamaBackend(model="test-model")
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        return _fake_response({"message": {"content": "ok"}})

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        backend.complete("sys prompt", "user prompt")

    assert captured["url"] == f"{DEFAULT_BASE_URL}/api/chat"
    assert captured["body"]["model"] == "test-model"
    assert captured["body"]["messages"] == [
        {"role": "system", "content": "sys prompt"},
        {"role": "user", "content": "user prompt"},
    ]
    assert captured["body"]["stream"] is False


def test_unreachable_server_raises_helpful_error():
    import urllib.error

    backend = OllamaBackend()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("connection refused")):
        with pytest.raises(OllamaNotReachableError, match="ollama pull"):
            backend.complete("system", "user")
