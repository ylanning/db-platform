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
from app.utils.logging import log_request_info

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
    with log_request_info(db_id=req.db_id, operation="provision", owner=req.owner):
        logger.info("Provisioning endpoint called")
        return await ProvisionerService().provision(req)


@router.post("/deprovision", response_model=ProvisionResponse)
async def deprovision(req: ProvisionRequest) -> ProvisionResponse:
    with log_request_info(db_id=req.db_id, owner=req.owner):
        logger.info(f"Deprovisioning {req.db_id} for {req.owner}")
        return await ProvisionerService().deprovision(req)


@router.get("/status/{db_id}", response_model=StatusResponse)
async def status(db_id: str) -> StatusResponse:
    return await ProvisionerService().status(db_id)


@router.post("/backup", response_model=BackupResponse)
async def backup(req: BackupRequest) -> BackupResponse:
    return await BackupService().backup(req)


@router.post("/rotate-credentials", response_model=RotateCredentialsResponse)
async def rotate_credentials(
    req: RotateCredentialsRequest,
) -> RotateCredentialsResponse:
    return await ProvisionerService().rotate_credentials(req)
