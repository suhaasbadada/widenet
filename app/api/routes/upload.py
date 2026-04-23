from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.authz import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.schemas.profile import ProfileResponse
from app.services import resume_service

router = APIRouter(prefix="/upload", tags=["upload"])

_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}


@router.post("/resume", response_model=dict)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Upload a resume file and receive a fully parsed candidate profile.

    Accepts PDF and DOCX files. The file is stored in Supabase Storage,
    text is extracted, and the profile is generated via AI then persisted.
    """
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Only PDF and DOCX are accepted.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        profile = resume_service.process_resume_upload(
            db=db,
            file_bytes=file_bytes,
            content_type=file.content_type,
            user_id=current_user.user_id,
        )
    except resume_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"success": True, "data": ProfileResponse.model_validate(profile).model_dump()}
