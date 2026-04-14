import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    user_id: uuid.UUID
    resume_url: str | None = None
    raw_resume: str | None = None
    structured_profile: dict[str, Any] | None = None
    headline: str | None = None
    summary: str | None = None


class ProfileUpdate(BaseModel):
    resume_url: str | None = None
    raw_resume: str | None = None
    structured_profile: dict[str, Any] | None = None
    headline: str | None = None
    summary: str | None = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_url: str | None
    raw_resume: str | None
    structured_profile: dict[str, Any] | None
    headline: str | None
    summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
