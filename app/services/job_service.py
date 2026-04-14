from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate


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
