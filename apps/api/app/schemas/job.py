import uuid
from datetime import datetime

from pydantic import BaseModel


class JobCreate(BaseModel):
    title: str
    company: str
    description: str | None = None


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
