import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.outreach import OutreachGenerateRequest, OutreachGenerateResponse
from app.services import ai_service


class ProfileNotFoundError(LookupError):
    """Raised when a user has no uploaded profile to personalize outreach."""


def generate_cold_email(
    db: Session,
    user_id: uuid.UUID,
    payload: OutreachGenerateRequest,
) -> OutreachGenerateResponse:
    """Generate a cold outreach email from the user's latest resume profile and a JD."""
    profile = db.scalar(
        select(Profile)
        .where(Profile.user_id == user_id)
        .order_by(Profile.created_at.desc())
    )
    if profile is None:
        raise ProfileNotFoundError(
            "No profile found for this user. Upload a resume before generating outreach."
        )

    structured_profile = profile.structured_profile or {
        "headline": profile.headline,
        "summary": profile.summary,
        "skills": [],
        "experience": [],
    }

    outreach = ai_service.generate_outreach(
        profile=structured_profile,
        job_title=payload.job_title,
        company=payload.company,
        job_description=payload.job_description,
    )

    return OutreachGenerateResponse(
        subject=str(outreach.get("subject", "")).strip(),
        message=str(outreach.get("message", "")).strip(),
    )
