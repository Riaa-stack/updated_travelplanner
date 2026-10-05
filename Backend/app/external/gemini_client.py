"""OpenRouter-backed LLM client.

The class keeps the historical ``GeminiClient`` name so existing
agent/test imports continue to work, but requests are now sent to OpenRouter.
"""

import time
from typing import Optional

import requests
from flask import current_app


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter cannot complete an LLM request."""


class GeminiClient:
    """Backward-compatible GeminiClient backed by OpenRouter."""

    def __init__(self):
        self.api_key = current_app.config.get("OPENROUTER_API_KEY")

        self.model = current_app.config.get(
            "OPENROUTER_MODEL",
            "google/gemini-3.8-flash",
        )

        self.fallback_model = current_app.config.get(
            "OPENROUTER_FALLBACK_MODEL",
            "google/gemini-3.7-flash",
        )

        self.base_url = current_app.config.get(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        ).rstrip("/")

        self.timeout = current_app.config.get(
            "OPENROUTER_TIMEOUT",
            90,
        )

        # Maximum output tokens.
        # We intentionally cap this at 8000.
        configured_tokens = current_app.config.get(
            "OPENROUTER_MAX_OUTPUT_TOKENS",
            8000,
        )

        try:
            configured_tokens = int(configured_tokens)
        except (TypeError, ValueError):
            configured_tokens = 8000

        self.max_output_tokens = min(configured_tokens, 8000)

        if not self.api_key:
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not configured. "
                "Add it to Backend/.env."
            )

        print("\n==============================")
        print("AI PROVIDER: OpenRouter")
        print("MODEL:", self.model)

        if self.fallback_model:
            print("FALLBACK:", self.fallback_model)

        print("MAX OUTPUT TOKENS:", self.max_output_tokens)
        print("==============================\n")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        retries: int = 1,
    ) -> str:
        """Generate JSON text through OpenRouter.

        429 errors are not blindly retried because repeated requests
        can consume additional quota/credits.

        Temporary network and server errors may be retried once.
        """

        if temperature is None:
            temperature = current_app.config.get(
                "OPENROUTER_TEMPERATURE",
                0.7,
            )

        # If caller provides a value, use it, but never allow more than 8000.
        if max_output_tokens is None:
            max_output_tokens = self.max_output_tokens
        else:
            try:
                max_output_tokens = int(max_output_tokens)
            except (TypeError, ValueError):
                max_output_tokens = self.max_output_tokens

            max_output_tokens = min(max_output_tokens, 8000)

        models = [self.model]

        if (
            self.fallback_model
            and self.fallback_model != self.model
        ):
            models.append(self.fallback_model)

        payload = {
            "models": models,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": temperature,
            "max_tokens": max_output_tokens,
            "response_format": {
                "type": "json_object",
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": current_app.config.get(
                "OPENROUTER_HTTP_REFERER",
                "http://localhost:5000",
            ),
            "X-OpenRouter-Title": current_app.config.get(
                "OPENROUTER_APP_TITLE",
                "AI Travel Planner",
            ),
        }

        url = f"{self.base_url}/chat/completions"

        total_attempts = max(1, int(retries))

        for attempt in range(total_attempts):
            print(
                f"OpenRouter attempt "
                f"{attempt + 1}/{total_attempts}"
            )

            try:
                print("Sending request to OpenRouter...")

                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )

                # ---------------------------------------------------------
                # RATE LIMIT / QUOTA
                # ---------------------------------------------------------
                if response.status_code == 429:
                    try:
                        detail = response.json()
                    except ValueError:
                        detail = response.text

                    raise OpenRouterError(
                        "OpenRouter rate limit or quota exceeded.\n"
                        f"Details: {detail}"
                    )

                # ---------------------------------------------------------
                # CREDIT ERROR
                # ---------------------------------------------------------
                if response.status_code == 402:
                    try:
                        detail = response.json()
                    except ValueError:
                        detail = response.text

                    raise OpenRouterError(
                        "OpenRouter does not have enough credits "
                        "for this request.\n"
                        f"Details: {detail}\n\n"
                        "Try lowering OPENROUTER_MAX_OUTPUT_TOKENS "
                        "or add OpenRouter credits."
                    )

                # ---------------------------------------------------------
                # SERVER ERRORS
                # ---------------------------------------------------------
                if response.status_code >= 500:
                    response.raise_for_status()

                # ---------------------------------------------------------
                # OTHER HTTP ERRORS
                # ---------------------------------------------------------
                if not response.ok:
                    try:
                        detail = response.json()
                    except ValueError:
                        detail = response.text

                    raise OpenRouterError(
                        f"OpenRouter request failed "
                        f"({response.status_code}): {detail}"
                    )

                # ---------------------------------------------------------
                # PARSE RESPONSE
                # ---------------------------------------------------------
                try:
                    data = response.json()
                except ValueError as exc:
                    raise OpenRouterError(
                        "OpenRouter returned invalid JSON."
                    ) from exc

                choices = data.get("choices") or []

                if not choices:
                    raise OpenRouterError(
                        "OpenRouter returned no choices."
                    )

                message = choices[0].get("message") or {}

                content = message.get("content")

                if not content:
                    raise OpenRouterError(
                        "OpenRouter returned an empty response."
                    )

                # ---------------------------------------------------------
                # SUCCESS
                # ---------------------------------------------------------
                print("Received response from OpenRouter")

                print(
                    "Model used:",
                    data.get("model", self.model),
                )

                usage = data.get("usage") or {}

                if usage:
                    print("Usage:", usage)

                return content

            except OpenRouterError:
                # Do not retry quota / credit / API errors blindly.
                raise

            except (
                requests.Timeout,
                requests.ConnectionError,
            ) as exc:

                print(
                    "OpenRouter network error:",
                    exc,
                )

                if attempt >= total_attempts - 1:
                    raise OpenRouterError(
                        f"Could not reach OpenRouter: {exc}"
                    ) from exc

                time.sleep(2)

            except requests.HTTPError as exc:

                print(
                    "OpenRouter HTTP error:",
                    exc,
                )

                if attempt >= total_attempts - 1:
                    raise OpenRouterError(
                        f"OpenRouter server error: {exc}"
                    ) from exc

                time.sleep(2)

        raise OpenRouterError(
            "OpenRouter request failed."
        )


# -------------------------------------------------------------------------
# Backward compatibility
# -------------------------------------------------------------------------
# Existing agents can continue importing GeminiClient.
# New code can use OpenRouterClient.
# -------------------------------------------------------------------------

OpenRouterClient = GeminiClient