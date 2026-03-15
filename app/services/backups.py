"""Service for creating PostgreSQL database backups in Cloud SQL."""

import structlog

from app.models.schemas import BackupRequest, BackupResponse
from app.services.sqladmin import CloudPostgresqlAdminClient

logger = structlog.get_logger(__name__)


class BackupService:
    """Creates on-demand backups of Cloud SQL PostgreSQL databases.

    This service wraps the Cloud SQL Admin API to trigger backup operations.
    Backups are stored in Google Cloud Storage and managed by Cloud SQL.

    Example:
        >>> from app.models.schemas import BackupRequest
        >>> svc = BackupService()
        >>> req = BackupRequest(db_id="orders-db")
        >>> resp = await svc.backup(req)
        >>> print(resp.backup_id)
        'backup-20260315-143022'
    """

    async def backup(self, req: BackupRequest) -> BackupResponse:
        """Create an on-demand backup of the specified database.

        Args:
            req: Backup request containing the db_id to back up.

        Returns:
            BackupResponse with the generated backup_id.

        Example:
            >>> req = BackupRequest(db_id="users-db")
            >>> resp = await svc.backup(req)
            >>> resp.backup_id
            'backup-20260315-143022'
        """
        sql = CloudPostgresqlAdminClient()
        backup_id = sql.create_backup(req.db_id)
        logger.info("Backup created", db_id=req.db_id, backup_id=backup_id)
        return BackupResponse(db_id=req.db_id, status="completed", backup_id=backup_id)
