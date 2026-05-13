import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job import JobCreate, JobResponse
from app.core.authz import AuthenticatedUser, get_current_user
from app.services import job_service, workday_skills_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=dict, status_code=201)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Save a job description and return its id for downstream flows."""
    job = job_service.create_job(db=db, payload=payload, user_id=current_user.user_id)
    return {"success": True, "data": JobResponse.model_validate(job).model_dump()}


@router.get("", response_model=dict)
def list_jobs(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """List all saved jobs for the current user."""
    jobs = job_service.get_jobs(db=db, user_id=current_user.user_id)
    data = [JobResponse.model_validate(job).model_dump() for job in jobs]
    return {"success": True, "data": data}


@router.get("/{job_id}", response_model=dict)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Fetch a single saved job by id for the current user."""
    try:
        job = job_service.get_job_by_id(db=db, job_id=job_id, user_id=current_user.user_id)
    except job_service.JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": JobResponse.model_validate(job).model_dump()}


@router.get("/{job_id}/workday-skills", response_model=dict)
def get_workday_skills(
    job_id: uuid.UUID,
    max_skills: int = Query(default=30, ge=10, le=60),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Generate a copy-pasteable Workday skills list for the selected job."""
    try:
        response = workday_skills_service.generate_workday_skills(
            db=db,
            user_id=current_user.user_id,
            job_id=job_id,
            max_skills=max_skills,
        )
    except job_service.JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except workday_skills_service.WorkdaySkillsGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {"success": True, "data": response.model_dump()}

