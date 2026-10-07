"""
Central configuration loaded from environment variables (.env).
Import `settings` anywhere you need config instead of calling os.getenv directly.
"""
import os
from dotenv import load_dotenv

load_dotenv()


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
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")
    USER_API_KEY: str = os.getenv("USER_API_KEY", "")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    TWILIO_SID: str = os.getenv("TWILIO_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_API_KEY_SID: str = os.getenv("TWILIO_API_KEY_SID", "")
    TWILIO_API_KEY_SECRET: str = os.getenv("TWILIO_API_KEY_SECRET", "")
    TWILIO_PHONE: str = os.getenv("TWILIO_PHONE", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
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

    def validate_production(self) -> None:
        self.validate()
        missing = []
        if not self.SUPABASE_SERVICE_ROLE_KEY:
            missing.append("SUPABASE_SERVICE_ROLE_KEY (required for server-side database writes)")
        if len(self.ADMIN_API_KEY) < 32:
            missing.append("ADMIN_API_KEY (use a randomly generated value of at least 32 characters)")
        if len(self.USER_API_KEY) < 32:
            missing.append("USER_API_KEY (use a randomly generated value of at least 32 characters)")
        if not self.JWT_SECRET or len(self.JWT_SECRET) < 32 or self.JWT_SECRET == "dev-secret-change-me":
            missing.append("JWT_SECRET (use a randomly generated value of at least 32 characters)")
        if not self.ALLOWED_ORIGINS or any("localhost" in origin or "127.0.0.1" in origin for origin in self.ALLOWED_ORIGINS):
            missing.append("ALLOWED_ORIGINS (production frontend origins only)")
        if not self.ALLOWED_HOSTS or "*" in self.ALLOWED_HOSTS:
            missing.append("ALLOWED_HOSTS (production API hostnames only)")
        if missing:
            raise RuntimeError("Production configuration is incomplete: " + "; ".join(missing))


settings = Settings()
