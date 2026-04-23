import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.profile import Profile
from app.models.user import User
from app.schemas.job_match import JobMatchItem, JobMatchResponse
from app.services import ai_service


class UserNotFoundError(LookupError):
    """Raised when job matching is requested for a missing user."""


class ProfileNotFoundError(LookupError):
    """Raised when a user has no profile for matching."""


def match_jobs_to_user(db: Session, user_id: uuid.UUID) -> JobMatchResponse:
    """Score all jobs against the user's latest structured profile."""
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User '{user_id}' does not exist.")

    profile = db.scalar(
        select(Profile).where(Profile.user_id == user_id).order_by(Profile.created_at.desc())
    )
    if profile is None:
        raise ProfileNotFoundError(
            "No profile found for this user. Upload a resume before job matching."
        )

    jobs = list(db.scalars(select(Job).order_by(Job.created_at.desc())).all())
    profile_context = profile.structured_profile or {
        "headline": profile.headline,
        "summary": profile.summary,
        "skills": [],
        "experience": [],
    }

    matches: list[JobMatchItem] = []
    for job in jobs:
        scored = ai_service.score_job_match(
            profile=profile_context,
            job_title=job.title,
            company=job.company,
            job_description=job.description or "",
        )
        matches.append(
            JobMatchItem(
                job_id=job.id,
                title=job.title,
                company=job.company,
                match_score=int(scored.get("match_score", 0)),
                reasoning=str(scored.get("reasoning", "")).strip(),
                skills_matched=[str(item) for item in scored.get("skills_matched", [])],
            )
        )

    matches.sort(key=lambda item: item.match_score, reverse=True)
    return JobMatchResponse(matches=matches)
