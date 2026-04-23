from typing import Any

from pydantic import BaseModel


class ResumeRenderDocxRequest(BaseModel):
    resume_json: Any
    template_path: str = "app/resume-templates/Template1.docx"
    file_name: str = "resume.docx"


class ResumeRenderPdfRequest(ResumeRenderDocxRequest):
    """Backward-compatible alias for older imports during DOCX-only phase."""
