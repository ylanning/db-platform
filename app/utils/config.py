from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DBP_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    project_id: str | None = None
    region: str = "europe-west2"
    instance_id: str | None = None
    backup_bucket: str | None = None
    secret_prefix: str = "dbp"
    request_timeout: int | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
