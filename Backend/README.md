
## AI provider configuration (OpenRouter)

The normal `/api/trips/plan` workflow now uses **one AI request per trip** through OpenRouter instead of making separate LLM calls for preference, budget, route chunks, crowd analysis, and travel-companion tips.

OpenRouter provides an OpenAI-compatible API and supports Google Gemini models through a single endpoint. See the official OpenRouter quickstart for the current API format and model catalog.

### Setup

1. Create an OpenRouter API key.
2. Copy `.env.example` to `.env`.
3. Set:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-3.8-flash
OPENROUTER_FALLBACK_MODEL=google/gemini-3.7-flash
```

4. Install backend requirements:

```powershell
pip install -r requirements.txt
```

5. Start the backend:

```powershell
python run.py
```

### Important

Do not put API keys directly into Python source code or commit `.env` to Git.

The older `GeminiClient` import is retained for compatibility, but it now sends requests through OpenRouter. The normal trip orchestrator calls `TripPlannerAgent` once and then enriches the result with Geoapify and OpenWeather.
