"""
Application settings — loaded from .env file via pydantic-settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Resolve .env relative to this file's directory (backend/app/../.env)
ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # AI
    gemini_api_key: str = ""

    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # Email
    resend_api_key: str = ""

    # App
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test_mode(self) -> bool:
        return self.razorpay_key_id.startswith("rzp_test_")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
