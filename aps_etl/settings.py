"""Application settings for APS ETL."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )

    database_url: str = Field(
        default="postgresql+psycopg://aps:aps@localhost:5432/aps", alias="DATABASE_URL"
    )
    aps_base_url: str = Field(default="https://adams-api.nrc.gov", alias="APS_BASE_URL")
    aps_primary_key: str = Field(alias="APS_PRIMARY_KEY")
    aps_secondary_key: str | None = Field(default=None, alias="APS_SECONDARY_KEY")

    vcr_record_mode: str = Field(default="none", alias="VCR_RECORD_MODE")
    vcr_cassette_dir: str = Field(default="tests/fixtures/cassettes", alias="VCR_CASSETTE_DIR")

    request_timeout_s: float = Field(default=30.0)
    retry_max_attempts: int = Field(default=3)
    retry_min_wait_s: float = Field(default=0.5)
    retry_max_wait_s: float = Field(default=5.0)

    max_pages_per_window: int = Field(default=200)
