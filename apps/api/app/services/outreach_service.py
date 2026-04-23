import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.outreach import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    OutreachCopilotRequest,
    OutreachCopilotResponse,
    OutreachGenerateRequest,
    OutreachGenerateResponse,
)
from app.services import ai_service


class ProfileNotFoundError(LookupError):
    """Raised when a user has no uploaded profile to personalize outreach."""


class CopilotTaskValidationError(ValueError):
    """Raised when task-specific required inputs are missing."""


def generate_cover_letter(
    db: Session,
    user_id: uuid.UUID,
    payload: CoverLetterGenerateRequest,
) -> CoverLetterGenerateResponse:
    """Generate a personalized cover letter from latest profile + job context."""
    profile = db.scalar(
        select(Profile)
        .where(Profile.user_id == user_id)
        .order_by(Profile.created_at.desc())
    )
    if profile is None:
        raise ProfileNotFoundError(
            "No profile found for this user. Upload a resume before generating a cover letter."
        )

    structured_profile = profile.structured_profile or {
        "headline": profile.headline,
        "summary": profile.summary,
        "skills": [],
        "experience": [],
    }

    generated = ai_service.generate_cover_letter(
        profile=structured_profile,
        job_title=payload.job_title,
        company=payload.company,
        job_description=payload.job_description,
        company_context=payload.company_context,
    )

    return CoverLetterGenerateResponse(
        cover_letter=str(generated.get("cover_letter", "")).strip()
    )


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


def generate_copilot_output(
    db: Session,
    user_id: uuid.UUID,
    payload: OutreachCopilotRequest,
) -> OutreachCopilotResponse:
    """Generate job-copilot output grounded in stored profile + JD context."""
    profile = db.scalar(
        select(Profile)
        .where(Profile.user_id == user_id)
        .order_by(Profile.created_at.desc())
    )
    if profile is None:
        raise ProfileNotFoundError(
            "No profile found for this user. Upload a resume before using copilot generation."
        )

    if payload.task == "job_answer" and not payload.question:
        raise CopilotTaskValidationError("Field 'question' is required for task 'job_answer'.")

    structured_profile = profile.structured_profile or {
        "headline": profile.headline,
        "summary": profile.summary,
        "skills": [],
        "experience": [],
    }

    generated = ai_service.generate_job_copilot_output(
        profile=structured_profile,
        task=payload.task,
        job_title=payload.job_title,
        job_description=payload.job_description,
        company=payload.company,
        company_context=payload.company_context,
        question=payload.question,
        user_instruction=payload.user_instruction,
    )

    return OutreachCopilotResponse(output=str(generated.get("output", "")).strip())
