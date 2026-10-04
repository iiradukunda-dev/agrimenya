"""
Central configuration loaded from environment variables (.env).
Import `settings` anywhere you need config instead of calling os.getenv directly.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "sb_secret_x47UXU8CNfsm8Pml7044ww_1VkTKgw9")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "sb_secret_x47UXU8CNfsm8Pml7044ww_1VkTKgw9")
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
        if origin.strip()
    ]
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")
    USER_API_KEY: str = os.getenv("USER_API_KEY", "")
    TWILIO_SID: str = os.getenv("TWILIO_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE: str = os.getenv("TWILIO_PHONE", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    DEFAULT_NOTIFICATION_EMAIL: str = os.getenv("DEFAULT_NOTIFICATION_EMAIL", "")
    DEFAULT_NOTIFICATION_PHONE: str = os.getenv("DEFAULT_NOTIFICATION_PHONE", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    APP_ENV: str = os.getenv("APP_ENV", "development")

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


settings = Settings()
