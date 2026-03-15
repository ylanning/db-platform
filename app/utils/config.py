"""Application configuration loaded from environment variables."""

from dataclasses import field
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingConfigDict


class DatabaseSettings(BaseSettings):
    """Database and GCP settings loaded from DBP_* environment variables.

    Env vars:
        DBP_PROJECT_ID - GCP project ID
        DBP_REGION - GCP region (default: europe-west2)
        DBP_INSTANCE_ID - Cloud SQL instance ID
        DBP_BACKUP_BUCKET - GCS bucket for backups
        DBP_SECRET_PREFIX - Prefix for secrets (default: dbs)
    """

    project_id: str = field(None, description="GCP project ID for the database")
    region: str = "europe-west2"
    instance_id: str | None = field(None, description="Cloud SQL instance ID")
    backup_bucket: str | None = field(
        None, description="GCS bucket for storing database backups"
    )
    secret_prefix: str = field(
        "dbs", description="Prefix for secrets storing database credentials"
    )

    model_config = SettingConfigDict(env_prefix="DBP_", case_sensitive=False)


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    """Return cached DatabaseSettings instance."""
    return DatabaseSettings()
