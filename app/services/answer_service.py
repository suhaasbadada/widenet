from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.profile import Profile
from app.schemas.answer import AnswerGenerateRequest, AnswerGenerateResponse
from app.services import ai_service


class ProfileNotFoundError(LookupError):
    """Raised when no profile exists for the requested user."""


class JobNotFoundError(LookupError):
    """Raised when the target job does not exist."""


def generate_answer(db: Session, payload: AnswerGenerateRequest) -> AnswerGenerateResponse:
    """Generate a job-specific answer using DB-backed profile and job context."""
    profile = db.scalar(
        select(Profile)
        .where(Profile.user_id == payload.user_id)
        .order_by(Profile.created_at.desc())
    )
    if profile is None:
        raise ProfileNotFoundError(
            "No profile found for this user. Upload a resume before generating answers."
        )

    job = db.get(Job, payload.job_id)
    if job is None:
        raise JobNotFoundError(f"Job '{payload.job_id}' does not exist.")

    profile_context = profile.structured_profile or {
        "headline": profile.headline,
        "summary": profile.summary,
        "skills": [],
        "experience": [],
    }

    generated = ai_service.generate_answer(
        profile=profile_context,
        job_title=job.title,
        job_description=job.description or "",
        question=payload.question,
    )

    return AnswerGenerateResponse(answer=str(generated.get("answer", "")).strip())
