import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationUpdate


class UserNotFoundError(LookupError):
    """Raised when an application references a missing user."""


class JobNotFoundError(LookupError):
    """Raised when an application references a missing job."""


class ApplicationNotFoundError(LookupError):
    """Raised when a requested application does not exist."""


class DuplicateApplicationError(ValueError):
    """Raised when a user already has an application for a job."""


def validate_no_duplicate_application(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> None:
    """Ensure the same user cannot apply to the same job multiple times."""
    existing = db.scalar(
        select(Application).where(
            Application.user_id == user_id,
            Application.job_id == job_id,
        )
    )
    if existing is not None:
        raise DuplicateApplicationError(
            f"Application already exists for user '{user_id}' and job '{job_id}'."
        )


def create_application(db: Session, payload: ApplicationCreate) -> Application:
    """Create an application after validating references and duplicates."""
    user = db.get(User, payload.user_id)
    if user is None:
        raise UserNotFoundError(f"User '{payload.user_id}' does not exist.")

    job = db.get(Job, payload.job_id)
    if job is None:
        raise JobNotFoundError(f"Job '{payload.job_id}' does not exist.")

    validate_no_duplicate_application(db=db, user_id=payload.user_id, job_id=payload.job_id)

    application = Application(
        user_id=payload.user_id,
        job_id=payload.job_id,
        status=payload.status,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def get_applications(db: Session, user_id: uuid.UUID | None = None) -> list[Application]:
    """List applications, optionally filtered by user."""
    query = select(Application)
    if user_id is not None:
        query = query.where(Application.user_id == user_id)
    query = query.order_by(Application.created_at.desc())
    return list(db.scalars(query).all())


def get_application_by_id(db: Session, application_id: uuid.UUID) -> Application:
    """Fetch a single application by id."""
    application = db.get(Application, application_id)
    if application is None:
        raise ApplicationNotFoundError(f"Application '{application_id}' does not exist.")
    return application


def update_application_status(
    db: Session,
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
) -> Application:
    """Update only the application status field."""
    application = get_application_by_id(db=db, application_id=application_id)
    application.status = payload.status
    db.commit()
    db.refresh(application)
    return application
