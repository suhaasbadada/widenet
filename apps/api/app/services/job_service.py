import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate


class JobNotFoundError(LookupError):
    """Raised when a requested job does not exist."""



def create_job(db: Session, payload: JobCreate, user_id: uuid.UUID) -> Job:
    """Persist a job description and return the created job record."""
    job = Job(
        user_id=user_id,
        title=payload.title.strip(),
        company=payload.company.strip(),
        description=payload.description,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job



def get_jobs(db: Session, user_id: uuid.UUID) -> list[Job]:
    """Return all jobs for a user ordered by recency."""
    return list(db.scalars(select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())).all())



def get_job_by_id(db: Session, job_id: uuid.UUID, user_id: uuid.UUID) -> Job:
    """Fetch a single job by id for a user."""
    job = db.get(Job, job_id)
    if job is None or job.user_id != user_id:
        raise JobNotFoundError(f"Job '{job_id}' does not exist for this user.")
    return job
