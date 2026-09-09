from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Hollywood"
    api_prefix: str = "/api"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    database_url: str = "sqlite+aiosqlite:///./hollywood.db"
    output_root: Path = Path("./projects")
    checkpoint_database_path: Path = Path("./.hollywood-checkpoints.sqlite")

    openai_api_key: str | None = None
    openai_llm_model: str = "gpt-4.1-mini"
    openai_image_model: str = "gpt-image-1"
    google_api_key: str | None = None
    google_video_model: str = "veo-3.1-generate-preview"

    wan_mode: str = "remote"
    wan_api_url: str | None = None
    wan_api_key: str | None = None
    wan_local_url: str = "http://localhost:7860"
    wan_model: str | None = None
    wan_backend: str = "rest"
    video_provider_order: list[str] = Field(default_factory=lambda: ["google", "wan_remote", "wan_local"])

    max_parallel_image_jobs: int = 2
    max_parallel_video_jobs: int = 2
    max_generation_retries: int = 3
    demo_mode: bool = False

    @field_validator("cors_origins", "video_provider_order", mode="before")
    @classmethod
    def split_csv(cls, value: str | list[str]) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()] if isinstance(value, str) else value

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
