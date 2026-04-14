import uuid
from datetime import datetime

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    user_id: uuid.UUID
    job_id: uuid.UUID
    status: str = "applied"


class ApplicationUpdate(BaseModel):
    status: str


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
