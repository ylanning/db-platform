from dataclasses import field
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingConfigDict


class DatabaseSettings(BaseSettings):
    project_id: str = field(None, description="GCP project ID for the database")
    region: str = "europe-west2"
    instance_id: str = field(None, description="Cloud SQL instance ID")
    backup_bucket: str = field(
        None, description="GCS bucket name for storing database backups"
    )
    secret_prefix: str = field(
        "dbs", description="Prefix for secrets storing database credentials"
    )

    model_config = SettingConfigDict(env_prefix="DBP_", case_sensitive=False)


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    """
    Return the DatabaseSettings object corresponding to the current environment in which the API
    """
    return DatabaseSettings()
