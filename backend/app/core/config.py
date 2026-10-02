"""
Central configuration loaded from environment variables (.env).
Import `settings` anywhere you need config instead of calling os.getenv directly.
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
        if origin.strip()
    ]
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    def validate(self) -> None:
        missing = []
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Copy .env.example to .env and fill them in."
            )


settings = Settings()
