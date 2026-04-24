from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask

from app.core.authz import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.schemas.resume_schema import (
    ExistingResumeResponse,
    ResumeGenerateFileRequest,
    ResumeGenerateRequest,
    ResumeGenerateResponse,
)
from app.schemas.resume_render_schema import ResumeRenderDocxRequest, ResumeRenderPdfRequest
from app.services import resume_render_service, resume_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("/me", response_model=dict)
def get_existing_resume(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return the latest uploaded resume/profile for the authenticated user."""
    try:
        resume = resume_service.get_existing_resume_for_user(db=db, user_id=current_user.user_id)
    except resume_service.ProfileNotFoundError as exc:
        return JSONResponse(status_code=404, content={"success": False, "error": str(exc)})

    return {"success": True, "data": ExistingResumeResponse.model_validate(resume).model_dump()}


@router.post("/generate", response_model=dict)
def generate_tailored_resume(
    payload: ResumeGenerateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Generate a tailored resume JSON from the caller's latest stored profile and a JD."""
    try:
        response = resume_service.generate_tailored_resume_from_registered_profile(
            db=db,
            user_id=current_user.user_id,
            job_description=payload.job_description,
            profile_overrides=payload.profile_overrides,
            template_path=payload.template_path,
            docx_file_name=payload.docx_file_name,
            pdf_file_name=payload.pdf_file_name,
        )
    except resume_service.ProfileNotFoundError as exc:
        return JSONResponse(status_code=404, content={"success": False, "error": str(exc)})
    except resume_service.ResumeGenerationValidationError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except resume_service.ResumeGenerationFailedError as exc:
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})

    return {"success": True, "data": response.model_dump()}


@router.post("/generate-file", response_model=None)
@router.post("/render-file", response_model=None)
def generate_and_render_resume_file(
    payload: ResumeGenerateFileRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Generate and render a tailored resume directly to DOCX/PDF in one call.

    The default output format is PDF when omitted in request payload.
    """
    try:
        artifact = resume_service.generate_and_render_resume_from_registered_profile(
            db=db,
            user_id=current_user.user_id,
            job_description=payload.job_description,
            output_format=payload.output_format,
            file_name=payload.file_name,
            profile_overrides=payload.profile_overrides,
            template_path=payload.template_path,
            docx_file_name=payload.docx_file_name,
            pdf_file_name=payload.pdf_file_name,
        )
    except resume_service.ProfileNotFoundError as exc:
        return JSONResponse(status_code=404, content={"success": False, "error": str(exc)})
    except resume_service.ResumeGenerationValidationError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except resume_render_service.ResumeRenderValidationError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except (resume_service.ResumeGenerationFailedError, resume_render_service.ResumeRenderFailedError) as exc:
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})

    return FileResponse(
        path=artifact.output_path,
        media_type=artifact.media_type,
        filename=artifact.download_name,
        background=BackgroundTask(artifact.temp_dir.cleanup),
    )


@router.post("/render-docx", response_model=None)
def render_resume_docx(
    payload: ResumeRenderDocxRequest,
    _: AuthenticatedUser = Depends(get_current_user),
) -> FileResponse:
    """Render resume JSON into DOCX using a DOCX template."""
    try:
        artifact = resume_render_service.render_resume_to_docx(
            resume_json=payload.resume_json,
            template_path=payload.template_path,
            file_name=payload.file_name,
        )
    except resume_render_service.ResumeRenderValidationError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except resume_render_service.ResumeRenderFailedError as exc:
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})

    filename = payload.file_name.strip() if payload.file_name else "resume.docx"
    if not filename.lower().endswith(".docx"):
        filename = f"{filename}.docx"

    return FileResponse(
        path=artifact.docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
        background=BackgroundTask(artifact.temp_dir.cleanup),
    )


@router.post("/render-pdf", response_model=None)
def render_resume_pdf(
    payload: ResumeRenderPdfRequest,
    _: AuthenticatedUser = Depends(get_current_user),
) -> FileResponse:
    """Render resume JSON into PDF using a DOCX template."""
    try:
        artifact = resume_render_service.render_resume_to_pdf(
            resume_json=payload.resume_json,
            template_path=payload.template_path,
            file_name=payload.file_name,
        )
    except resume_render_service.ResumeRenderValidationError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except resume_render_service.ResumeRenderFailedError as exc:
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})

    filename = payload.file_name.strip() if payload.file_name else "resume.pdf"
    if not filename.lower().endswith(".pdf"):
        filename = f"{filename}.pdf"

    return FileResponse(
        path=artifact.pdf_path,
        media_type="application/pdf",
        filename=filename,
        background=BackgroundTask(artifact.temp_dir.cleanup),
    )
