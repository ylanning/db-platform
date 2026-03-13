import logging

from app.models.schemas import ProvisionRequest, ProvisionResponse
from app.models.sqladmin import CloudPostgresqlAdminClient
from app.services.secrets import SecretManagerService

logger = logging.getLogger(__name__)


class ProvisionerService:
    async def provision(self, req: ProvisionRequest) -> ProvisionResponse:
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
        return ProvisionResponse(db_id=req.db_id, status="deprovisioned")
