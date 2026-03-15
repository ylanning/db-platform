"""Client for managing databases and users in Cloud SQL PostgreSQL."""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.utils.config import get_database_settings


class CloudPostgresqlAdminClient:
    """Wraps Cloud SQL Admin API for database, user, and backup operations.

    Usage:
        sql = CloudPostgresqlAdminClient()
        sql.create_database("mydb")
        sql.create_user("myuser", "secure_password")
        backup_id = sql.create_backup("mydb")
    """

    def __init__(self) -> None:
        """Load project settings and create SQL Admin API client."""
        settings = get_database_settings()
        if not settings.project_id or not settings.instance_id:
            raise RuntimeError("Missing project_id or instance_id in database settings")
        self.project_id = settings.project_id
        self.instance_id = settings.instance_id
        self._service = build("sqladmin", "v1", cache_discovery=False)

    def create_database(self, db_name: str) -> None:
        """Create a new database in the Cloud SQL instance."""
        body = {"name": db_name}
        request = self._service.databases().insert(
            project=self.project_id, instance=self.instance_id, body=body
        )
        request.execute()

    def delete_database(self, db_name: str) -> None:
        """Delete a database from the Cloud SQL instance."""
        request = self._service.databases().delete(
            project=self.project_id, instance=self.instance_id, database=db_name
        )
        request.execute()

    def create_user(self, user_name: str, password: str) -> None:
        """Create a database user with the given password."""
        body = {"name": user_name, "password": password}
        request = self._service.users().insert(
            project=self.project_id, instance=self.instance_id, body=body
        )
        request.execute()

    def delete_user(self, user_name: str) -> None:
        """Delete a database user."""
        request = self._service.users().delete(
            project=self.project_id, instance=self.instance_id, name=user_name, host="%"
        )
        request.execute()

    def update_user_password(self, user_name: str, password: str) -> None:
        """Update a database user's password."""
        body = {"name": user_name, "password": password}
        request = self._service.users().update(
            project=self.project_id,
            instance=self.instance_id,
            name=user_name,
            host="%",
            body=body,
        )
        request.execute()

    def create_backup(self, db_name: str) -> str:
        """Create an on-demand backup. Returns the backup ID."""
        request = (
            self._service.instances()
            .backuprun()
            .insert(
                project=self.project_id,
                instance=self.instance_id,
                body={"description": f"Backup for {db_name}"},
            )
        )
        response = request.execute()
        return str(response.get("id", ""))

    def get_backup_status(self, backup_id: str) -> str:
        """Get the status of a backup operation."""
        request = (
            self._service.instances()
            .backuprun()
            .get(project=self.project_id, instance=self.instance_id, id=backup_id)
        )
        response = request.execute()
        return response.get("status", "")

    def is_upstream_error(self, exc: Exception) -> bool:
        return self._status_code(exc) in {500, 502, 503}

    def is_not_found(self, exc: Exception) -> bool:
        return self._status_code(exc) == 404

    def _status_code(self, exc: Exception) -> int | None:
        if not isinstance(exc, HttpError):
            return None
        if hasattr(exc, "status_code"):
            return exc.status_code
        if hasattr(exc, "resp") and hasattr(exc.resp, "status"):
            return int(exc.resp.status)
        return None
