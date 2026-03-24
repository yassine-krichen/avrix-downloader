from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Avrix Sidecar Backend"
    app_env: str = "dev"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    api_prefix: str = "/api/v1"

    config_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3] / "config")

    model_config = SettingsConfigDict(
        env_prefix="AVRIX_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
