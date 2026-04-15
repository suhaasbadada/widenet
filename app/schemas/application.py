import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    user_id: uuid.UUID
    job_id: uuid.UUID
    status: Literal["applied", "interview", "rejected", "offer"] = "applied"


class ApplicationUpdate(BaseModel):
    status: Literal["applied", "interview", "rejected", "offer"]


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    status: Literal["applied", "interview", "rejected", "offer"]
    created_at: datetime

    model_config = {"from_attributes": True}
