from typing import Literal

from pydantic import BaseModel, Field


class OutreachGenerateRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=2, max_length=200)
    job_description: str = Field(min_length=20)


class OutreachGenerateResponse(BaseModel):
    subject: str
    message: str


class CoverLetterGenerateRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=2, max_length=200)
    job_description: str = Field(min_length=20)
    company_context: str | None = None


class CoverLetterGenerateResponse(BaseModel):
    cover_letter: str


class OutreachCopilotRequest(BaseModel):
    task: Literal["job_answer", "cover_letter", "resume_improve", "cold_outreach"]
    job_title: str = Field(min_length=2, max_length=200)
    job_description: str = Field(min_length=20)
    company: str | None = Field(default=None, max_length=200)
    company_context: str | None = None
    question: str | None = None
    user_instruction: str | None = None


class OutreachCopilotResponse(BaseModel):
    output: str
