import uuid
from urllib.parse import urlparse

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.services import ai_service
from app.utils.file_parser import extract_text


class ProfileNotFoundError(LookupError):
    """Raised when a user has no stored profile."""


class ProfileRefreshError(ValueError):
    """Raised when profile refresh cannot obtain resume text to reprocess."""


def get_profile_by_user(db: Session, user_id: uuid.UUID) -> Profile:
    """Fetch the latest profile for a user."""
    profile = db.scalar(
        select(Profile).where(Profile.user_id == user_id).order_by(Profile.created_at.desc())
    )
    if profile is None:
        raise ProfileNotFoundError(f"No profile found for user '{user_id}'.")
    return profile


def refresh_profile(db: Session, user_id: uuid.UUID) -> Profile:
    """Re-run AI structuring against stored resume data for a user profile."""
    profile = get_profile_by_user(db=db, user_id=user_id)

    raw_resume = profile.raw_resume
    if not raw_resume and profile.resume_url:
        response = requests.get(profile.resume_url, timeout=30)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type") or _content_type_from_url(profile.resume_url)
        raw_resume = extract_text(file_bytes=response.content, content_type=content_type)

    if not raw_resume:
        raise ProfileRefreshError(
            "Profile cannot be refreshed because no raw resume text or downloadable resume file is available."
        )

    parsed = ai_service.parse_resume(raw_resume=raw_resume)
    profile.raw_resume = raw_resume
    profile.structured_profile = parsed
    profile.headline = parsed.get("headline")
    profile.summary = parsed.get("summary")

    db.commit()
    db.refresh(profile)
    return profile


def _content_type_from_url(url: str) -> str:
    """Infer resume MIME type from URL path when headers are unavailable."""
    path = urlparse(url).path.lower()
    if path.endswith(".pdf"):
        return "application/pdf"
    if path.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if path.endswith(".doc"):
        return "application/msword"
    raise ProfileRefreshError("Unsupported resume file type for profile refresh.")
