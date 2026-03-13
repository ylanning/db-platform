"""Service for provisioning and deprovisioning PostgreSQL databases."""

import logging

from app.models.schemas import ProvisionRequest, ProvisionResponse
from app.models.sqladmin import CloudPostgresqlAdminClient
from app.services.secrets import SecretManagerService

logger = logging.getLogger(__name__)


class ProvisionerService:
    """Handles database lifecycle operations: provisioning and deprovisioning.

    This service orchestrates creating/deleting databases, users, and secrets
    in Google Cloud SQL and Secret Manager.

    Example:
        >>> from app.models.schemas import ProvisionRequest
        >>> svc = ProvisionerService()
        >>> req = ProvisionRequest(db_id="myapp-prod", owner="team-backend")
        >>> response = await svc.provision(req)
        >>> print(response.status)
        'provisioned'
        >>> print(response.connection_secret_name)
        'projects/my-project/secrets/dbplatform-myapp-prod-conn'
    """

    async def provision(self, req: ProvisionRequest) -> ProvisionResponse:
        """Create a new database with user and store credentials in Secret Manager.

        Steps performed:
            1. Generate a secure password
            2. Create the database in Cloud SQL
            3. Create a user with the generated password
            4. Store the connection string in Secret Manager

        Args:
            req: Provision request containing db_id and owner.

        Returns:
            ProvisionResponse with status='provisioned' and the secret name.

        Example:
            >>> req = ProvisionRequest(db_id="orders-db", owner="team-orders")
            >>> resp = await svc.provision(req)
            >>> resp.status
            'provisioned'
        """
        logger.info(f"Provisioning {req.db_id}")
        sql = CloudPostgresqlAdminClient()
        secrets = SecretManagerService()
        db_name = req.db_id
        user_name = f"user_{req.db_id}"

        password = secrets.generate_password()
        sql.create_database(db_name)
        sql.create_user(user_name, password)

        conn_string = f"postgresql://{user_name}:{password}@/{db_name}"
        secret_name = secrets.create_or_update_secret(req.db_id, conn_string)

        logger.info(f"Provisioned {req.db_id} Owner: {req.owner} ")
        return ProvisionResponse(
            db_id=req.db_id, status="provisioned", connection_secret_name=secret_name
        )

    async def deprovision(self, req: ProvisionRequest) -> ProvisionResponse:
        """Remove a database, its user, and associated secret.

        Steps performed:
            1. Delete the database from Cloud SQL (ignores if not found)
            2. Delete the user from Cloud SQL (ignores if not found)
            3. Delete the secret from Secret Manager

        Args:
            req: Provision request containing db_id and owner.

        Returns:
            ProvisionResponse with status='deprovisioned'.

        Example:
            >>> req = ProvisionRequest(db_id="orders-db", owner="team-orders")
            >>> resp = await svc.deprovision(req)
            >>> resp.status
            'deprovisioned'
        """
        logger.info(f"Deprovisioning {req.db_id}")
        sql = CloudPostgresqlAdminClient()
        secrets = SecretManagerService()
        db_name = req.db_id
        user_name = f"user_{req.db_id}"

        try:
            sql.delete_database(db_name)
        except Exception as exc:
            if not sql.is_not_found(exc):
                logger.error(f"Error deleting database {db_name}", exc_info=exc)
                raise

        try:
            sql.delete_user(user_name)
        except Exception as exc:
            if not sql.is_not_found(exc):
                logger.error(f"Error deleting user {user_name}", exc_info=exc)
                raise

        try:
            secrets.delete_secret(req.db_id)
        except Exception as exc:
            logger.error(f"Error deleting secret {req.db_id}", exc_info=exc)
            pass

        logger.info(f"Deprovisioned {req.db_id} Owner: {req.owner}")
        return ProvisionResponse(
            db_id=req.db_id, status="deprovisioned", connection_secret_name=None
        )
