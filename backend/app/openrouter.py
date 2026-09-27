import json
from collections.abc import Callable
from typing import Any

import httpx


OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"


class OpenRouterError(RuntimeError):
    """Base error for safe, user-facing OpenRouter failures."""


class OpenRouterConfigurationError(OpenRouterError):
    """Raised when the provider is not configured."""


class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None,
        *,
        model: str = OPENROUTER_MODEL,
        timeout: float = 20.0,
        transport: httpx.BaseTransport | None = None,
        client_factory: Callable[..., httpx.Client] = httpx.Client,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.client = client_factory(timeout=timeout, transport=transport)

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "OpenRouterClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def complete(self, prompt: str) -> str:
        return self.complete_messages(
            [{"role": "user", "content": prompt}],
        )

    def complete_json(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
    ) -> dict[str, Any]:
        content = self.complete_messages(
            messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "kanban_assistant_response",
                    "strict": True,
                    "schema": response_schema,
                },
            },
        )
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as error:
            raise OpenRouterError("OpenRouter returned invalid JSON") from error
        if not isinstance(payload, dict):
            raise OpenRouterError("OpenRouter returned an invalid JSON object")
        return payload

    def complete_messages(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        if not self.api_key:
            raise OpenRouterConfigurationError(
                "OPENROUTER_API_KEY is not configured"
            )

        try:
            response = self.client.post(
                OPENROUTER_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    **({"response_format": response_format} if response_format else {}),
                },
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except httpx.TimeoutException as error:
            raise OpenRouterError("OpenRouter request timed out") from error
        except httpx.HTTPStatusError as error:
            raise OpenRouterError(
                f"OpenRouter returned HTTP {error.response.status_code}"
            ) from error
        except httpx.RequestError as error:
            raise OpenRouterError("OpenRouter request failed") from error
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise OpenRouterError("OpenRouter returned an invalid response") from error

        if not isinstance(content, str) or not content.strip():
            raise OpenRouterError("OpenRouter returned an empty response")
        return content.strip()


def ask_openrouter(prompt: str, api_key: str | None) -> str:
    with OpenRouterClient(api_key) as client:
        return client.complete(prompt)
