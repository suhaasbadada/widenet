from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job_match import JobMatchRequest
from app.services import job_match_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/match", response_model=dict)
def match_jobs(payload: JobMatchRequest, db: Session = Depends(get_db)) -> dict:
    """Score all jobs against a user's latest profile."""
    try:
        matches = job_match_service.match_jobs_to_user(db=db, user_id=payload.user_id)
    except job_match_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except job_match_service.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": matches.model_dump()}
