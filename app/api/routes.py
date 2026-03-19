import logging

from fastapi import APIRouter

from app.models.schemas import (
    BackupRequest,
    BackupResponse,
    ProvisionRequest,
    ProvisionResponse,
    RotateCredentialsRequest,
    RotateCredentialsResponse,
    StatusResponse,
)
from app.services.backups import BackupService
from app.services.provisioner import ProvisionerService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "OK"}


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post("/provision", response_model=ProvisionResponse)
async def provision(req: ProvisionRequest) -> ProvisionResponse:
    logger.info("Provisioning endpoint called")
    return await ProvisionerService().run_provision(req)


@router.post("/deprovision", response_model=ProvisionResponse)
async def deprovision(req: ProvisionRequest) -> ProvisionResponse:
    logger.info(f"Deprovisioning {req.db_id} for {req.owner}")
    return await ProvisionerService().run_deprovision(req)


@router.get("/status/{db_id}", response_model=StatusResponse)
async def status(db_id: str) -> StatusResponse:
    logger.info(f"Getting status for {db_id}")
    return await ProvisionerService().run_status(db_id)


@router.post("/backup", response_model=BackupResponse)
async def backup(req: BackupRequest) -> BackupResponse:
    logger.info(f"Backing up {req.db_id} for {req.owner}")
    return await BackupService().backup(req)


@router.post("/rotate-credentials", response_model=RotateCredentialsResponse)
async def rotate_credentials(
    req: RotateCredentialsRequest,
) -> RotateCredentialsResponse:
    logger.info(f"Rotating credentials for {req.db_id}")
    return await ProvisionerService().run_rotate_credentials(req)
