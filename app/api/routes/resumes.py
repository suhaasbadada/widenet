import uuid

from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse

from app.core.security import InvalidTokenError, SecurityConfigurationError, decode_access_token
from app.db.session import get_db
from app.schemas.resume_schema import (
    ExistingResumeResponse,
    ResumeGenerateRequest,
    ResumeGenerateResponse,
)
from app.services import resume_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/resumes", tags=["resumes"])
_bearer_scheme = HTTPBearer(auto_error=True)


def _resolve_user_id(credentials: HTTPAuthorizationCredentials) -> tuple[uuid.UUID | None, str | None, int | None]:
    try:
        token_payload = decode_access_token(credentials.credentials)
        return uuid.UUID(str(token_payload["sub"])), None, None
    except (InvalidTokenError, ValueError) as exc:
        return None, str(exc), 401
    except SecurityConfigurationError as exc:
        return None, str(exc), 500


@router.get("/me", response_model=dict)
def get_existing_resume(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """Return the latest uploaded resume/profile for the authenticated user."""
    user_id, error_message, status = _resolve_user_id(credentials)
    if error_message is not None and status is not None:
        return JSONResponse(status_code=status, content={"success": False, "error": error_message})

    try:
        resume = resume_service.get_existing_resume_for_user(db=db, user_id=user_id)
    except resume_service.ProfileNotFoundError as exc:
        return JSONResponse(status_code=404, content={"success": False, "error": str(exc)})

    return {"success": True, "data": ExistingResumeResponse.model_validate(resume).model_dump()}


@router.post("/generate", response_model=dict)
def generate_tailored_resume(
    payload: ResumeGenerateRequest,
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """Generate a tailored resume JSON from the caller's latest stored profile and a JD."""
    user_id, error_message, status = _resolve_user_id(credentials)
    if error_message is not None and status is not None:
        return JSONResponse(status_code=status, content={"success": False, "error": error_message})

    try:
        response = resume_service.generate_tailored_resume_from_registered_profile(
            db=db,
            user_id=user_id,
            job_description=payload.job_description,
        )
    except resume_service.ProfileNotFoundError as exc:
        return JSONResponse(status_code=404, content={"success": False, "error": str(exc)})
    except resume_service.ResumeGenerationValidationError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except resume_service.ResumeGenerationFailedError as exc:
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})

    return {"success": True, "data": response.model_dump()}
