"""Service for managing database credentials in Google Cloud Secret Manager."""

import secrets

from google.cloud import secretmanager
from app.utils.config import get_database_settings


class SecretManagerService:
    """Manages database connection secrets in Google Cloud Secret Manager.

    This service handles creating, updating, and deleting secrets that store
    database connection strings. Each secret is named using the pattern:
    {secret_prefix}-{db_id}-conn

    Example:
        >>> svc = SecretManagerService()
        >>> password = svc.generate_password()
        >>> conn_str = f"postgresql://user:{password}@localhost/mydb"
        >>> secret_name = svc.create_or_update_secret("mydb-001", conn_str)
        >>> print(secret_name)
        projects/my-project/secrets/dbplatform-mydb-001-conn
    """

    def __init__(self) -> None:
        """Initialize the service with project settings and Secret Manager client.

        Raises:
            RuntimeError: If project_id is not configured in database settings.
        """
        settings = get_database_settings()
        if not settings.project_id:
            raise RuntimeError("Missing project_id in database settings")
        self.project_id = settings.project_id
        self.secret_prefix = settings.secret_prefix
        self._client = secretmanager.SecretManagerServiceClient()

    def _secret_id(self, db_id: str) -> str:
        """Build the secret ID from a database identifier."""
        return f"{self.secret_prefix}-{db_id}-conn"

    def create_or_update_secret(self, db_id: str, value: str) -> str:
        """Store a connection string as a secret, creating the secret if needed.

        Args:
            db_id: Database identifier used to build the secret name.
            value: The connection string to store.

        Returns:
            The full resource name of the secret (e.g., projects/X/secrets/Y).

        Example:
            >>> svc = SecretManagerService()
            >>> svc.create_or_update_secret("prod-db", "postgresql://...")
            'projects/my-project/secrets/dbplatform-prod-db-conn'
        """
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
        """Delete the secret associated with a database.

        Args:
            db_id: Database identifier whose secret should be deleted.

        Example:
            >>> svc = SecretManagerService()
            >>> svc.delete_secret("prod-db")  # Removes the secret entirely
        """
        name = f"projects/{self.project_id}/secrets/{self._secret_id(db_id)}"
        self._client.delete_secret(request={"name": name})

    def generate_password(self) -> str:
        """Generate a cryptographically secure 32-character password.

        Example:
            >>> svc = SecretManagerService()
            >>> svc.generate_password()
            'aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY'
        """
        return secrets.token_urlsafe(24)
