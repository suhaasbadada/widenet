import uuid

from pydantic import BaseModel, Field


class AnswerGenerateRequest(BaseModel):
    user_id: uuid.UUID
    job_id: uuid.UUID
    question: str = Field(min_length=5)


class AnswerGenerateResponse(BaseModel):
    answer: str
