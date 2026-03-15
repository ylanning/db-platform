from fastapi import APIRouter, HTTPException

from app.models.schemas import ProvisionResponse, ProvisionRequest, StatusResponse
from app.services.sqladmin import CloudSqlAdminClient

from app.services.provisioner import ProvisionerService

router = APIRouter()


@router.get("/")
async def health_check():
    return {"message": "OK"}


@router.post("/provision", response_model=ProvisionResponse)
async def provision(req: ProvisionRequest) -> ProvisionResponse:
    return await ProvisionerService().provision(req)


@router.post("/deprovision", response_model=ProvisionResponse)
async def deprovision(req: ProvisionRequest) -> ProvisionResponse:
    return await ProvisionerService().deprovision(req)


@router.get("/status/{db_id}", response_model=StatusResponse)
async def status(db_id: str) -> StatusResponse:
    return await ProvisionerService().status(db_id)
