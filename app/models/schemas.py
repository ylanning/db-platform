from pydantic import BaseModel, Field


class ProvisionRequest(BaseModel):
    db_id: str = Field(..., description="Logical database id")
    owner: str = Field(..., description="Owning team or service")
    tier: str = Field("standard", description="Service tier")


class ProvisionResponse(BaseModel):
    db_id: str = Field(..., description="Logical database id")
    status: str = Field(..., description="Provision status")
    connection_secret_name: str = Field(None, description="Connection secret name")


class StatusResponse(BaseModel):
    db_id: str = Field(..., description="Logical database id")
    status: str = Field(..., description="Provision status")
    message: str = Field(None, description="Provision status message")


class BackupRequest(BaseModel):
    db_id: str = Field(..., description="Logical database id")


class BackupResponse(BaseModel):
    db_id: str = Field(..., description="Logical database id")
    status: str = Field(..., description="Backup status")
    backup_id: str = Field(None, description="Backup id")


class RotateCredentialsRequest(BaseModel):
    db_id: str = Field(..., description="Logical database id")


class RotateCredentialsResponse(BaseModel):
    db_id: str = Field(..., description="Logical database id")
    status: str = Field(..., description="Rotate credentials status")
    secret_name: str = Field(None, description="Secret name")
