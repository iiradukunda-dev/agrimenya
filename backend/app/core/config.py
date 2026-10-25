"""
Central configuration loaded from environment variables (.env).
Import `settings` anywhere you need config instead of calling os.getenv directly.
"""
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Resolve the backend's own .env instead of depending on the caller's working
# directory (for example, when Uvicorn is launched from the repository root).
BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BACKEND_ROOT / ".env", override=False)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_KEY: str = SUPABASE_SERVICE_ROLE_KEY or os.getenv("SUPABASE_KEY", "")
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
        if origin.strip()
    ]
    ALLOWED_HOSTS: list[str] = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "*").split(",") if host.strip()]
    # Groq is the default chat provider because its developer free tier is
    # available for this project. Anthropic remains opt-in for compatibility.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    GROQ_VISION_MODEL: str = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    ADMIN_PASSWORD_RESET_URL: str = os.getenv("ADMIN_PASSWORD_RESET_URL", "").strip()
    COMMUNITY_PASSWORD_RESET_URL: str = os.getenv(
        "COMMUNITY_PASSWORD_RESET_URL", "http://localhost:8501/Community"
    ).strip()
    USER_API_KEY: str = os.getenv("USER_API_KEY", "")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    COMMUNITY_PHOTO_BUCKET: str = os.getenv("COMMUNITY_PHOTO_BUCKET", "community-field-reports").strip()
    TWILIO_SID: str = os.getenv("TWILIO_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_API_KEY_SID: str = os.getenv("TWILIO_API_KEY_SID", "")
    TWILIO_API_KEY_SECRET: str = os.getenv("TWILIO_API_KEY_SECRET", "")
    TWILIO_PHONE: str = os.getenv("TWILIO_PHONE", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    WHATSAPP_MODE: str = os.getenv("WHATSAPP_MODE", "mock").strip().lower()
    WHATSAPP_GRAPH_VERSION: str = os.getenv("WHATSAPP_GRAPH_VERSION", "").strip()
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    # Public E.164 sender number used for end-user click-to-chat links; not a secret.
    WHATSAPP_PUBLIC_NUMBER: str = os.getenv("WHATSAPP_PUBLIC_NUMBER", "").strip()
    WHATSAPP_PUBLIC_CHAT_ENABLED: bool = _env_bool("WHATSAPP_PUBLIC_CHAT_ENABLED", False)
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "").strip()
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_APP_SECRET: str = os.getenv("WHATSAPP_APP_SECRET", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    WHATSAPP_DEFAULT_COUNTRY_CODE: str = os.getenv("WHATSAPP_DEFAULT_COUNTRY_CODE", "250").strip()
    WHATSAPP_DAILY_CAP: int = int(os.getenv("WHATSAPP_DAILY_CAP", "200"))
    ALLOW_UNSIGNED_WEBHOOKS_IN_MOCK: bool = _env_bool("ALLOW_UNSIGNED_WEBHOOKS_IN_MOCK", False)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_SSL: bool = _env_bool("SMTP_USE_SSL", False)
    SMTP_STARTTLS: bool = _env_bool("SMTP_STARTTLS", True)
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    DEFAULT_NOTIFICATION_EMAIL: str = os.getenv("DEFAULT_NOTIFICATION_EMAIL", "")
    DEFAULT_NOTIFICATION_PHONE: str = os.getenv("DEFAULT_NOTIFICATION_PHONE", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    APP_ENV: str = os.getenv("APP_ENV", "development").strip().lower()

    def validate(self) -> None:
        missing = []
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY:
            missing.append("SUPABASE_KEY or SUPABASE_SERVICE_ROLE_KEY")
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Copy .env.example to .env and fill them in."
            )
        if self.MAX_UPLOAD_SIZE_MB < 1 or self.MAX_UPLOAD_SIZE_MB > 50:
            raise RuntimeError("MAX_UPLOAD_SIZE_MB must be between 1 and 50")
        if self.WHATSAPP_MODE not in {"mock", "live"}:
            raise RuntimeError("WHATSAPP_MODE must be either 'mock' or 'live'")
        if self.WHATSAPP_DAILY_CAP < 1:
            raise RuntimeError("WHATSAPP_DAILY_CAP must be at least 1")

    def validate_whatsapp(self) -> None:
        if self.WHATSAPP_MODE not in {"mock", "live"}:
            raise RuntimeError("WHATSAPP_MODE must be either 'mock' or 'live'")
        if self.WHATSAPP_MODE == "live":
            missing = [name for name in (
                "WHATSAPP_GRAPH_VERSION",
                "WHATSAPP_PHONE_NUMBER_ID",
                "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "WHATSAPP_ACCESS_TOKEN",
                "WHATSAPP_APP_SECRET",
                "WHATSAPP_VERIFY_TOKEN",
            ) if not getattr(self, name)]
            if missing:
                raise RuntimeError("Live WhatsApp mode requires: " + ", ".join(missing))

    def validate_production(self) -> None:
        self.validate()
        missing = []
        if not self.SUPABASE_SERVICE_ROLE_KEY:
            missing.append("SUPABASE_SERVICE_ROLE_KEY (required for server-side database writes)")
        if len(self.USER_API_KEY) < 32:
            missing.append("USER_API_KEY (use a randomly generated value of at least 32 characters)")
        if not self.JWT_SECRET or len(self.JWT_SECRET) < 32 or self.JWT_SECRET == "dev-secret-change-me":
            missing.append("JWT_SECRET (use a randomly generated value of at least 32 characters)")
        if (not self.ALLOWED_ORIGINS or "*" in self.ALLOWED_ORIGINS or
                any("localhost" in origin or "127.0.0.1" in origin for origin in self.ALLOWED_ORIGINS)):
            missing.append("ALLOWED_ORIGINS (production frontend origins only)")
        if not self.ALLOWED_HOSTS or "*" in self.ALLOWED_HOSTS:
            missing.append("ALLOWED_HOSTS (production API hostnames only)")
        if self.JWT_ALGORITHM != "HS256":
            missing.append("JWT_ALGORITHM (only HS256 is supported)")
        reset_url = urlparse(self.ADMIN_PASSWORD_RESET_URL)
        if not self.SMTP_HOST or not self.EMAIL_FROM or reset_url.scheme != "https" or not reset_url.netloc:
            missing.append("SMTP_HOST, EMAIL_FROM, and HTTPS ADMIN_PASSWORD_RESET_URL (administrator password recovery)")
        community_reset_url = urlparse(self.COMMUNITY_PASSWORD_RESET_URL)
        if community_reset_url.scheme != "https" or not community_reset_url.netloc:
            missing.append("HTTPS COMMUNITY_PASSWORD_RESET_URL (farmer account recovery)")
        if missing:
            raise RuntimeError("Production configuration is incomplete: " + "; ".join(missing))


settings = Settings()
