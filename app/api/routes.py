from fastapi import APIRouter, HTTPException

from app.models.schemas import ProvisionResponse, ProvisionRequest
from app.services.sqladmin import CloudSqlAdminClient


router = APIRouter()


@router.get("/")
async def health_check():
    return {"message": "OK"}


# @router.post("/provision", response_model=ProvisionResponse)
# async def provision(request: ProvisionRequest) -> ProvisionResponse:
#     sql =
#     return ProvisionResponse()
