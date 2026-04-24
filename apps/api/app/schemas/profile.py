import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProfileLinkItem(BaseModel):
    type: str = Field(validation_alias="link_type")
    url: str
    is_primary: bool = False

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ProfileCreate(BaseModel):
    user_id: uuid.UUID
    resume_url: str | None = None
    raw_resume: str | None = None
    structured_profile: dict[str, Any] | None = None
    name: str | None = None
    contact_number: str | None = None
    links: list[str | ProfileLinkItem] | None = None
    headline: str | None = None
    summary: str | None = None


class ProfileUpdate(BaseModel):
    resume_url: str | None = None
    raw_resume: str | None = None
    structured_profile: dict[str, Any] | None = None
    name: str | None = None
    contact_number: str | None = None
    links: list[str | ProfileLinkItem] | None = None
    headline: str | None = None
    summary: str | None = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_url: str | None
    raw_resume: str | None
    structured_profile: dict[str, Any] | None
    name: str | None
    contact_number: str | None
    links: list[str] | None
    profile_links: list[ProfileLinkItem] | None = None
    headline: str | None
    summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
