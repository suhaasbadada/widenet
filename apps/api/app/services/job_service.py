import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate


class JobNotFoundError(LookupError):
    """Raised when a requested job does not exist."""


def create_job(db: Session, payload: JobCreate) -> Job:
    """Persist a job description and return the created job record."""
    job = Job(
        title=payload.title.strip(),
        company=payload.company.strip(),
        description=payload.description,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_jobs(db: Session) -> list[Job]:
    """Return all jobs ordered by recency."""
    return list(db.scalars(select(Job).order_by(Job.created_at.desc())).all())


def get_job_by_id(db: Session, job_id: uuid.UUID) -> Job:
    """Fetch a single job by id."""
    job = db.get(Job, job_id)
    if job is None:
        raise JobNotFoundError(f"Job '{job_id}' does not exist.")
    return job
