"""SARO Platform Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "SARO Platform"
    version: str = "4.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./saro.db"
    redis_url: str = "redis://redis:6379/0"

    # Auth
    secret_key: str = "saro-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Features
    enable_blockchain: bool = True
    enable_agentic: bool = True
    guardrail_latency_target_ms: int = 200

    class Config:
        env_file = ".env"


settings = Settings()
