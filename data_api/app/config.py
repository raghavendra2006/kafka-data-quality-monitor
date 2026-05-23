"""Application configuration loaded from environment variables."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://warehouse_user:warehouse_pass@postgres-warehouse:5432/warehouse_db"
    DATABASE_URL_SYNC: str = "postgresql://warehouse_user:warehouse_pass@postgres-warehouse:5432/warehouse_db"

    # JWT
    JWT_SECRET: str = "super_secret_jwt_key_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
