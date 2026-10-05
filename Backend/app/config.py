import os
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------
    # OpenRouter AI configuration
    # ------------------------------------------------------------------
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1",
    )
    OPENROUTER_MODEL = os.getenv(
        "OPENROUTER_MODEL",
        "google/gemini-3.8-flash",
    )
    OPENROUTER_FALLBACK_MODEL = os.getenv(
        "OPENROUTER_FALLBACK_MODEL",
        "google/gemini-3.7-flash",
    )
    OPENROUTER_TEMPERATURE = float(
        os.getenv("OPENROUTER_TEMPERATURE", "0.3")
    )
    OPENROUTER_MAX_OUTPUT_TOKENS = int(
        os.getenv("OPENROUTER_MAX_OUTPUT_TOKENS", "12000")
    )
    OPENROUTER_TIMEOUT = int(
        os.getenv("OPENROUTER_TIMEOUT", "90")
    )
    OPENROUTER_HTTP_REFERER = os.getenv(
        "OPENROUTER_HTTP_REFERER",
        "http://localhost:5000",
    )
    OPENROUTER_APP_TITLE = os.getenv(
        "OPENROUTER_APP_TITLE",
        "AI Travel Planner",
    )

    # Backward-compatible aliases for older code/tests.
    GEMINI_API_KEY = OPENROUTER_API_KEY
    GEMINI_MODEL = OPENROUTER_MODEL
    GEMINI_TEMPERATURE = OPENROUTER_TEMPERATURE
    GEMINI_MAX_OUTPUT_TOKENS = OPENROUTER_MAX_OUTPUT_TOKENS

    GEOAPIFY_API_KEY = GEOAPIFY_API_KEY
    OPENWEATHER_API_KEY = OPENWEATHER_API_KEY
    HOTEL_API_KEY = os.getenv("HOTEL_API_KEY")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
