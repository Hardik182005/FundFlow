"""Central runtime configuration for FundFlow.

Reads from environment variables (loaded from .env by main.py). No secrets are
hardcoded here. Import the singleton `settings` everywhere instead of calling
os.getenv directly so behaviour stays consistent and testable.
"""
import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # ---- Anakin ----
    ANAKIN_API_KEY: str = os.getenv("ANAKIN_API_KEY", "")
    ANAKIN_API_BASE: str = os.getenv("ANAKIN_API_BASE", "https://api.anakin.io/v1").rstrip("/")
    ANAKIN_TOTAL_CREDIT_BUDGET: int = _int("ANAKIN_TOTAL_CREDIT_BUDGET", 300)
    ANAKIN_MAX_CREDITS_PER_AUDIT: int = _int("ANAKIN_MAX_CREDITS_PER_AUDIT", 8)
    ANAKIN_MAX_WIRE_CREDITS_PER_CALL: int = _int("ANAKIN_MAX_WIRE_CREDITS_PER_CALL", 3)
    ANAKIN_CACHE_TTL_HOURS: int = _int("ANAKIN_CACHE_TTL_HOURS", 168)
    ANAKIN_SEARCH_CACHE_TTL_HOURS: int = _int("ANAKIN_SEARCH_CACHE_TTL_HOURS", 720)

    # Per-audit hard limits
    MAX_FRESH_SCRAPER_URLS: int = _int("ANAKIN_MAX_FRESH_SCRAPER_URLS", 4)
    MAX_WIRE_ACTIONS_PER_AUDIT: int = _int("ANAKIN_MAX_WIRE_ACTIONS_PER_AUDIT", 1)
    MAX_SEARCH_CALLS_PER_AUDIT: int = _int("ANAKIN_MAX_SEARCH_CALLS_PER_AUDIT", 1)

    # Wire action overrides (logical name -> action id)
    WIRE_ACTION_OVERRIDES = {
        "fund_profile": os.getenv("WIRE_ACTION_FUND_PROFILE", ""),
        "fund_holdings": os.getenv("WIRE_ACTION_FUND_HOLDINGS", ""),
        "fund_manager_news": os.getenv("WIRE_ACTION_MANAGER_NEWS", ""),
        "security_profile": os.getenv("WIRE_ACTION_SECURITY_PROFILE", ""),
        "security_market_cap": os.getenv("WIRE_ACTION_MARKET_CAP", ""),
    }

    # ---- LLMs ----
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ---- ElevenLabs ----
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")
    ELEVENLABS_TTS_MODEL: str = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_turbo_v2_5")

    # ---- Runtime ----
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    PORT: int = _int("PORT", 8080)

    # ---- Demo ----
    DEMO_MODE: bool = _bool("FUNDFLOW_DEMO_MODE", True)

    @property
    def anakin_configured(self) -> bool:
        return bool(self.ANAKIN_API_KEY)


settings = Settings()
