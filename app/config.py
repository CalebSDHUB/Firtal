from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # Agent model
    anthropic_model: str = "claude-3-haiku-20240307"

    # Agent guardrails
    max_tokens_per_response: int = 512
    max_turns_per_conversation: int = 10
    max_requests_per_minute: int = 20

    # App
    app_version: str = "1.0.0"
    environment: str = "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
