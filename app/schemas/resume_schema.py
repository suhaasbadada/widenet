from typing import Any

from pydantic import BaseModel, Field


class ResumeGenerateRequest(BaseModel):
    job_description: str = Field(min_length=20)


class ResumeGenerateResponse(BaseModel):
    tailored_resume: dict[str, Any]


class ExistingResumeResponse(BaseModel):
    resume_url: str | None
    raw_resume: str | None
    structured_profile: dict[str, Any]
    headline: str | None
    summary: str | None
