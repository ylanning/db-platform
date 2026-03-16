"""Service for provisioning and deprovisioning PostgreSQL databases."""

import logging

from app.models.schemas import (
    ProvisionRequest,
    ProvisionResponse,
    RotateCredentialsRequest,
    RotateCredentialsResponse,
    StatusResponse,
)
from app.services.errors import UpstreamError
from app.services.secrets import SecretManagerService
from app.services.sqladmin import CloudPostgresqlAdminClient
from app.utils.async_utils import run_with_timeout

logger = logging.getLogger(__name__)


class ProvisionerService:
    """Manages database lifecycle in Cloud SQL and Secret Manager.

    Usage:
        svc = ProvisionerService()
        req = ProvisionRequest(db_id="myapp", owner="team-backend")
        resp = await svc.provision(req)  # Creates db, user, and secret
        resp = await svc.deprovision(req)  # Removes all resources
    """

    async def provision(self, req: ProvisionRequest) -> ProvisionResponse:
        """Create database, user, and store connection string in Secret Manager."""
        logger.info(f"Provisioning {req.db_id}")
        sql = CloudPostgresqlAdminClient()
        secrets = SecretManagerService()
        db_name = req.db_id
        user_name = f"user_{req.db_id}"

        password = secrets.generate_password()
        try:
            await run_with_timeout(sql.create_database, db_name)
            await run_with_timeout(sql.create_user, user_name, password)
        except Exception as exc:
            if sql.is_upstream_error(exc):
                logger.error(f"Error provisioning {req.db_id}", exc_info=exc)
                raise UpstreamError(f"Failed to provision database: {exc}") from exc
            raise

        conn_string = f"postgresql://{user_name}:{password}@/{db_name}"
        secret_name = await run_with_timeout(
            secrets.create_or_update_secret, req.db_id, conn_string
        )

        logger.info(f"Provisioned {req.db_id} Owner: {req.owner} ")
        return ProvisionResponse(
            db_id=req.db_id, status="provisioned", connection_secret_name=secret_name
        )

    async def deprovision(self, req: ProvisionRequest) -> ProvisionResponse:
        """Delete database, user, and secret. Ignores resources not found."""
        logger.info(f"Deprovisioning {req.db_id}")
        sql = CloudPostgresqlAdminClient()
        secrets = SecretManagerService()
        db_name = req.db_id
        user_name = f"user_{req.db_id}"

        try:
            await run_with_timeout(sql.delete_database, db_name)
        except Exception as exc:
            if sql.is_upstream_error(exc):
                raise UpstreamError("cloud sql error") from exc
            raise

        try:
            await run_with_timeout(sql.delete_user, user_name)
        except Exception as exc:
            if sql.is_upstream_error(exc):
                logger.error(f"Error deleting user {user_name}", exc_info=exc)
                raise UpstreamError(f"Failed to delete user: {exc}") from exc
            raise

        try:
            await run_with_timeout(secrets.delete_secret, req.db_id)
        except Exception as exc:
            logger.warning(f"Error deleting secret {req.db_id}, continuing", exc_info=exc)

        logger.info(f"Deprovisioned {req.db_id} Owner: {req.owner}")
        return ProvisionResponse(
            db_id=req.db_id, status="deprovisioned", connection_secret_name=None
        )

    async def status(self, db_id: str) -> StatusResponse:
        """Check the status of a database provision."""
        logger.info(f"Checking status for {db_id}")
        return StatusResponse(db_id=db_id, status="provisioned", message="Implement health checks")

    async def rotate_credentials(self, req: RotateCredentialsRequest) -> RotateCredentialsResponse:
        """Rotate database credentials by generating a new password and updating the secret."""
        logger.info(f"Rotating credentials for {req.db_id}")
        sql = CloudPostgresqlAdminClient()
        secrets = SecretManagerService()
        user_name = f"user_{req.db_id}"
        password = secrets.generate_password()

        try:
            await run_with_timeout(sql.update_user_password, user_name, password)
        except Exception as exc:
            if sql.is_upstream_error(exc):
                logger.error(f"Error updating password for {user_name}", exc_info=exc)
                raise UpstreamError(f"Failed to rotate credentials: {exc}") from exc
            raise

        conn_string = f"postgresql://{user_name}:{password}@/{req.db_id}"
        secret_name = await run_with_timeout(
            secrets.create_or_update_secret, req.db_id, conn_string
        )

        logger.info(f"Rotated credentials for {req.db_id}")
        return RotateCredentialsResponse(db_id=req.db_id, status="rotated", secret_name=secret_name)
