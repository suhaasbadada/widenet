import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job import JobCreate, JobResponse
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=dict, status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db)) -> dict:
    """Save a job description and return its id for downstream flows."""
    job = job_service.create_job(db=db, payload=payload)
    return {"success": True, "data": JobResponse.model_validate(job).model_dump()}


@router.get("", response_model=dict)
def list_jobs(db: Session = Depends(get_db)) -> dict:
    """List all saved jobs."""
    jobs = job_service.get_jobs(db=db)
    data = [JobResponse.model_validate(job).model_dump() for job in jobs]
    return {"success": True, "data": data}


@router.get("/{job_id}", response_model=dict)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Fetch a single saved job by id."""
    try:
        job = job_service.get_job_by_id(db=db, job_id=job_id)
    except job_service.JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": JobResponse.model_validate(job).model_dump()}

