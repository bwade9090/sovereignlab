"""Typed application settings with safe secret handling."""

from enum import StrEnum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Supported runtime environments."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Load SovereignLab settings from environment variables or a local .env file."""

    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    mistral_api_key: SecretStr | None = Field(default=None, validation_alias="MISTRAL_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SOVEREIGNLAB_",
        extra="ignore",
    )
