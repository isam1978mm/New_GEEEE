from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GEE Screening Web App"
    data_dir: Path = Field(default=Path("./data"))
    database_path: Path = Field(default=Path("./data/gee_screening.db"))
    allow_network_bind: bool = Field(default=False)
    ee_service_account_email: str | None = Field(default=None)
    ee_service_account_key_path: Path | None = Field(default=None)
    ee_real_execution_enabled: bool = Field(default=False)
    notebook_reference_bundle_dir: Path | None = Field(default=None)

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.database_path.as_posix()}"

    @property
    def bind_host(self) -> str:
        return "0.0.0.0" if self.allow_network_bind else "127.0.0.1"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

