"""Service for creating PostgreSQL database backups in Cloud SQL."""

import structlog

from app.models.schemas import BackupRequest, BackupResponse
from app.services.sqladmin import CloudPostgresqlAdminClient

logger = structlog.get_logger(__name__)


class BackupService:
    """Creates on-demand backups of Cloud SQL PostgreSQL databases.

    Usage:
        svc = BackupService()
        req = BackupRequest(db_id="orders-db")
        resp = await svc.backup(req)
    """

    async def backup(self, req: BackupRequest) -> BackupResponse:
        """Trigger an on-demand backup and return the backup ID."""
        sql = CloudPostgresqlAdminClient()
        backup_id = sql.create_backup(req.db_id)
        logger.info("Backup created", db_id=req.db_id, backup_id=backup_id)
        return BackupResponse(db_id=req.db_id, status="completed", backup_id=backup_id)
