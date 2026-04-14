from pydantic import BaseModel, Field


class OutreachGenerateRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=2, max_length=200)
    job_description: str = Field(min_length=20)


class OutreachGenerateResponse(BaseModel):
    subject: str
    message: str
