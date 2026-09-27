import json

import httpx
import pytest

from app.openrouter import (
    OPENROUTER_ENDPOINT,
    OPENROUTER_MAX_COMPLETION_TOKENS,
    OPENROUTER_MODEL,
    OpenRouterClient,
    OpenRouterConfigurationError,
    OpenRouterError,
)


def test_missing_api_key_is_rejected_without_a_request() -> None:
    with OpenRouterClient(None, transport=httpx.MockTransport(lambda _: pytest.fail())) as client:
        with pytest.raises(OpenRouterConfigurationError):
            client.complete("2 + 2")


def test_successful_completion_uses_the_configured_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL(OPENROUTER_ENDPOINT)
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = request.read()
        assert OPENROUTER_MODEL.encode() in payload
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "4"}}]},
        )

    with OpenRouterClient("test-key", transport=httpx.MockTransport(handler)) as client:
        assert client.complete("2 + 2") == "4"


def test_provider_error_does_not_expose_response_body() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(503, text="private provider details")
    )

    with OpenRouterClient("test-key", transport=transport) as client:
        with pytest.raises(OpenRouterError, match="HTTP 503") as error:
            client.complete("2 + 2")

    assert "private provider details" not in str(error.value)


def test_timeout_is_reported_as_a_safe_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    with OpenRouterClient(
        "test-key", transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(OpenRouterError, match="timed out"):
            client.complete("2 + 2")


def test_json_completion_requests_strict_structured_output() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read())
        assert payload["max_completion_tokens"] == OPENROUTER_MAX_COMPLETION_TOKENS
        response_format = payload["response_format"]
        assert response_format["type"] == "json_schema"
        assert response_format["json_schema"]["strict"] is True
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"reply":"4"}'}}]},
        )

    with OpenRouterClient(
        "test-key", transport=httpx.MockTransport(handler)
    ) as client:
        assert client.complete_json(
            [{"role": "user", "content": "2 + 2"}],
            {"type": "object", "properties": {"reply": {"type": "string"}}},
        ) == {"reply": "4"}


def test_truncated_provider_response_is_reported() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": '{"reply":"incomplete"}'},
                    }
                ]
            },
        )
    )

    with OpenRouterClient("test-key", transport=transport) as client:
        with pytest.raises(OpenRouterError, match="truncated"):
            client.complete("2 + 2")
