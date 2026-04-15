import uuid

from pydantic import BaseModel, Field


class JobMatchRequest(BaseModel):
    user_id: uuid.UUID


class JobMatchItem(BaseModel):
    job_id: uuid.UUID
    title: str
    company: str
    match_score: int = Field(ge=0, le=100)
    reasoning: str
    skills_matched: list[str]


class JobMatchResponse(BaseModel):
    matches: list[JobMatchItem]
