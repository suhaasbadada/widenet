import uuid

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, SecurityConfigurationError, decode_access_token
from app.db.session import get_db
from app.schemas.outreach import (
    CoverLetterGenerateRequest,
    OutreachCopilotRequest,
    OutreachGenerateRequest,
)
from app.services import outreach_service

router = APIRouter(prefix="/outreach", tags=["outreach"])
_bearer_scheme = HTTPBearer(auto_error=True)


@router.post("/cover-letter", response_model=dict)
def generate_cover_letter(
    payload: CoverLetterGenerateRequest,
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """Generate a cover letter using the caller's latest profile and provided JD."""
    try:
        token_payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(str(token_payload["sub"]))
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except SecurityConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        response = outreach_service.generate_cover_letter(
            db=db,
            user_id=user_id,
            payload=payload,
        )
    except outreach_service.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": response.model_dump()}


@router.post("/cold-email", response_model=dict)
def generate_cold_email(
    payload: OutreachGenerateRequest,
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """Generate a recruiter cold email using the caller's latest resume profile and a JD."""
    try:
        token_payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(str(token_payload["sub"]))
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except SecurityConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        response = outreach_service.generate_cold_email(
            db=db,
            user_id=user_id,
            payload=payload,
        )
    except outreach_service.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": response.model_dump()}


@router.post("/copilot", response_model=dict)
def generate_copilot_output(
    payload: OutreachCopilotRequest,
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """Generate personalized job-copilot content for multiple writing tasks."""
    try:
        token_payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(str(token_payload["sub"]))
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except SecurityConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        response = outreach_service.generate_copilot_output(
            db=db,
            user_id=user_id,
            payload=payload,
        )
    except outreach_service.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except outreach_service.CopilotTaskValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"success": True, "data": response.model_dump()}
