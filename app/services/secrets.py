"""Service for managing database credentials in Google Cloud Secret Manager."""

import secrets

from google.cloud import secretmanager

from app.utils.config import get_settings


class SecretManagerService:
    """Stores database connection strings in Google Cloud Secret Manager.

    Secret naming: {secret_prefix}_{db_id}_conn

    Usage:
        svc = SecretManagerService()
        password = svc.generate_password()
        svc.create_or_update_secret("mydb", f"postgresql://user:{password}@host/db")
    """

    def __init__(self) -> None:
        """Load project settings and create Secret Manager client."""
        settings = get_settings()
        if not settings.project_id:
            raise RuntimeError("Missing project_id in database settings")
        self.project_id = settings.project_id
        self.secret_prefix = settings.secret_prefix
        self._client = secretmanager.SecretManagerServiceClient()

    def _secret_id(self, db_id: str) -> str:
        """Build the secret ID from a database identifier."""
        return f"{self.secret_prefix}_{db_id}_conn"

    def create_or_update_secret(self, db_id: str, value: str) -> str:
        """Store a connection string. Creates the secret if it doesn't exist."""
        secret_id = self._secret_id(db_id)
        parent = f"projects/{self.project_id}"
        name = f"{parent}/secrets/{secret_id}"

        try:
            self._client.get_secret(request={"name": name})
        except Exception:
            self._client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )

        self._client.add_secret_version(
            request={"parent": name, "payload": {"data": value.encode("utf-8")}}
        )
        return name

    def delete_secret(self, db_id: str) -> None:
        """Delete the secret for the given database."""
        name = f"projects/{self.project_id}/secrets/{self._secret_id(db_id)}"
        self._client.delete_secret(request={"name": name})

    def generate_password(self) -> str:
        """Generate a secure 32-character URL-safe password."""
        return secrets.token_urlsafe(24)
