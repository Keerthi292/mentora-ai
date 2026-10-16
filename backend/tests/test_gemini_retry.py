"""Gemini's brief 5xx errors are retried by the real SDK client (no network: a fake transport)."""

import httpx
import pytest
from google import genai
from google.genai import errors

from app.ai import llm_client

OK_BODY = {"candidates": [{"content": {"role": "model", "parts": [{"text": "OK"}]}}]}


def _client(statuses):
    """A real genai.Client whose HTTP responses come from `statuses` in order."""
    calls = []

    def handler(request):
        status = statuses[len(calls)]
        calls.append(status)
        if status == 200:
            return httpx.Response(200, json=OK_BODY)
        return httpx.Response(status, json={"error": {"code": status, "status": "UNAVAILABLE", "message": "overloaded"}})

    options = llm_client._http_options(10)
    options.retry_options.initial_delay = 0.01  # keep the test fast
    options.retry_options.max_delay = 0.02
    options.client_args = {"transport": httpx.MockTransport(handler)}
    return genai.Client(api_key="test-key-not-real", http_options=options), calls


def test_overloaded_once_then_succeeds():
    client, calls = _client([503, 200])

    response = client.models.generate_content(model="m", contents="hi")

    assert response.text == "OK"
    assert calls == [503, 200]


def test_gives_up_after_three_attempts():
    client, calls = _client([503, 500, 503, 200])

    with pytest.raises(errors.ServerError):
        client.models.generate_content(model="m", contents="hi")
    assert calls == [503, 500, 503]


def test_quota_errors_are_not_retried():
    client, calls = _client([429, 200])

    with pytest.raises(errors.ClientError):
        client.models.generate_content(model="m", contents="hi")
    assert calls == [429]
