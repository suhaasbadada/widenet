from typing import Any, Literal

from pydantic import BaseModel, Field


class ResumeProfileOverrides(BaseModel):
    name: str | None = None
    contact_number: str | None = None
    links: list[str] | None = None
    summary: str | None = None
    skills: dict[str, list[str]] | list[dict[str, Any]] | None = None
    experience: list[dict[str, Any]] | None = None
    projects: list[dict[str, Any]] | None = None
    education: list[dict[str, Any]] | None = None


class ResumeGenerateRequest(BaseModel):
    job_description: str = Field(min_length=20)
    profile_overrides: ResumeProfileOverrides | None = None
    template_path: str = "app/resume-templates/Template1.docx"
    docx_file_name: str = "resume.docx"
    pdf_file_name: str = "resume.pdf"


class ResumeGenerateFileRequest(ResumeGenerateRequest):
    output_format: Literal["docx", "pdf"] = "pdf"
    file_name: str | None = None


class ResumeRenderPayload(BaseModel):
    resume_json: dict[str, Any]
    template_path: str
    file_name: str


class ResumeLink(BaseModel):
    type: str
    url: str
    is_primary: bool = False


class ResumeGenerateResponse(BaseModel):
    tailored_resume: dict[str, Any]
    resume_json: dict[str, Any]
    render_docx_payload: ResumeRenderPayload
    render_pdf_payload: ResumeRenderPayload


class ExistingResumeResponse(BaseModel):
    resume_url: str | None
    raw_resume: str | None
    structured_profile: dict[str, Any]
    name: str | None
    contact_number: str | None
    links: list[str] | None
    profile_links: list[ResumeLink] | None = None
    headline: str | None
    summary: str | None
