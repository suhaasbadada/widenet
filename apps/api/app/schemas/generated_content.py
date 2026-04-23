import uuid
from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel


class GeneratedContentCreate(BaseModel):
    user_id: uuid.UUID
    job_id: uuid.UUID
    type: Literal["answer", "outreach"]
    content: dict[str, Any] | None = None


class GeneratedContentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    type: Literal["answer", "outreach"]
    content: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
