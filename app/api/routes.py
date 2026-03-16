from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ProvisionResponse,
    ProvisionRequest,
    StatusResponse,
    BackupResponse,
    BackupRequest,
    RotateCredentialsResponse,
    RotateCredentialsRequest,
)
from app.services.backups import BackupService

from app.services.provisioner import ProvisionerService

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "OK"}


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post("/provision", response_model=ProvisionResponse)
async def provision(req: ProvisionRequest) -> ProvisionResponse:
    return await ProvisionerService().provision(req)


@router.post("/deprovision", response_model=ProvisionResponse)
async def deprovision(req: ProvisionRequest) -> ProvisionResponse:
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
