"""Public OpenRouter client import.

The implementation lives in gemini_client.py for backwards compatibility with
existing project imports.
"""

from app.external.gemini_client import GeminiClient, OpenRouterClient, OpenRouterError

__all__ = ["GeminiClient", "OpenRouterClient", "OpenRouterError"]
