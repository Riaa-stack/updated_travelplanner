"""OpenRouter-backed LLM client.

The class keeps the historical ``GeminiClient`` name so existing agent/test
imports continue to work, but requests are sent to OpenRouter.
"""

import time
from typing import Optional

import requests
from flask import current_app


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter cannot complete an LLM request."""


class GeminiClient:
    """Backward-compatible client name backed by OpenRouter."""

    def __init__(self):
        self.api_key = current_app.config.get("OPENROUTER_API_KEY")
        self.model = current_app.config.get("OPENROUTER_MODEL")
        self.fallback_model = current_app.config.get("OPENROUTER_FALLBACK_MODEL")
        self.base_url = current_app.config.get(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        ).rstrip("/")
        self.timeout = current_app.config.get("OPENROUTER_TIMEOUT", 90)

        if not self.api_key:
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not configured. Add it to Backend/.env."
            )

        print("\n==============================")
        print("AI PROVIDER: OpenRouter")
        print("MODEL:", self.model)
        if self.fallback_model:
            print("FALLBACK:", self.fallback_model)
        print("==============================\n")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        retries: int = 1,
    ) -> str:
        """Generate a response through OpenRouter.

        429 errors are not blindly retried. Temporary 5xx/network failures
        can be retried when retries is greater than one.
        """

        if temperature is None:
            temperature = current_app.config["OPENROUTER_TEMPERATURE"]

        if max_output_tokens is None:
            max_output_tokens = current_app.config["OPENROUTER_MAX_OUTPUT_TOKENS"]

        models = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models.append(self.fallback_model)

        print(
            "OpenRouter prompt character count: "
            f"{len(system_prompt) + len(user_prompt)}"
        )

        payload = {
            "models": models,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_output_tokens,
            "response_format": {"type": "json_object"},
            # Supported by compatible models; reduces reasoning overhead.
            "reasoning": {"effort": "low"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": current_app.config.get(
                "OPENROUTER_HTTP_REFERER", "http://localhost:5000"
            ),
            "X-OpenRouter-Title": current_app.config.get(
                "OPENROUTER_APP_TITLE", "AI Travel Planner"
            ),
        }

        url = f"{self.base_url}/chat/completions"
        total_attempts = max(1, int(retries))

        for attempt in range(total_attempts):
            print(f"OpenRouter attempt {attempt + 1}/{total_attempts}")

            try:
                print("Sending request to OpenRouter...")
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code == 429:
                    raise OpenRouterError(
                        "OpenRouter rate limit/quota exceeded. Please wait "
                        "and try again, or use a model/provider with available quota."
                    )

                if response.status_code >= 500:
                    response.raise_for_status()

                if not response.ok:
                    try:
                        detail = response.json()
                    except ValueError:
                        detail = response.text
                    raise OpenRouterError(
                        f"OpenRouter request failed ({response.status_code}): {detail}"
                    )

                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    raise OpenRouterError("OpenRouter returned no choices.")

                content = choices[0].get("message", {}).get("content")
                if not content:
                    raise OpenRouterError("OpenRouter returned an empty response.")

                print("Received response from OpenRouter")
                print("Model used:", data.get("model", self.model))
                usage = data.get("usage") or {}
                if usage:
                    print("Usage:", usage)

                return content

            except OpenRouterError:
                raise
            except (requests.Timeout, requests.ConnectionError) as exc:
                print("OpenRouter network error:", exc)
                if attempt >= total_attempts - 1:
                    raise OpenRouterError(
                        f"Could not reach OpenRouter: {exc}"
                    ) from exc
                time.sleep(2)
            except requests.HTTPError as exc:
                print("OpenRouter HTTP error:", exc)
                if attempt >= total_attempts - 1:
                    raise OpenRouterError(
                        f"OpenRouter server error: {exc}"
                    ) from exc
                time.sleep(2)

        raise OpenRouterError("OpenRouter request failed.")


OpenRouterClient = GeminiClient
