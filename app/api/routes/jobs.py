from fastapi import APIRouter, Depends
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
