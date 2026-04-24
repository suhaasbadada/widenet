import uuid
from urllib.parse import urlparse

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.profile import ProfileUpdate
from app.services import ai_service, profile_link_service
from app.services.resume_service import (
    _enrich_education_from_raw_resume,
    _extract_contact_from_profile,
    _extract_contact_from_raw_resume,
    _extract_links_from_profile,
    _extract_links_from_raw_resume,
    _extract_name_from_profile,
    _extract_name_from_raw_resume,
)
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
    parsed_name = _extract_name_from_profile(parsed) or _extract_name_from_raw_resume(raw_resume)
    parsed_contact = _extract_contact_from_profile(parsed) or _extract_contact_from_raw_resume(raw_resume)
    parsed_links = _extract_links_from_profile(parsed) or _extract_links_from_raw_resume(raw_resume)

    if parsed_name and not parsed.get("name"):
        parsed["name"] = parsed_name
    if parsed_contact and not parsed.get("contact_number"):
        parsed["contact_number"] = parsed_contact
    if parsed_links and not parsed.get("links"):
        parsed["links"] = parsed_links
    parsed["links"] = _extract_links_from_profile(parsed) or parsed_links
    parsed["education"] = _enrich_education_from_raw_resume(parsed.get("education", []), raw_resume)

    profile.raw_resume = raw_resume
    profile.structured_profile = parsed
    profile.name = parsed_name or profile.name
    profile.contact_number = parsed_contact or profile.contact_number
    normalized_links = profile_link_service.normalize_links_payload(parsed_links)
    if normalized_links:
        profile.links = profile_link_service.normalize_links_for_legacy_column(normalized_links)
        profile_link_service.replace_profile_links(
            db=db,
            profile_id=profile.id,
            links=normalized_links,
        )
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


def update_latest_profile(db: Session, user_id: uuid.UUID, payload: ProfileUpdate) -> Profile:
    """Update mutable profile fields on the latest profile for a user."""
    profile = get_profile_by_user(db=db, user_id=user_id)

    if payload.resume_url is not None:
        profile.resume_url = payload.resume_url
    if payload.raw_resume is not None:
        profile.raw_resume = payload.raw_resume
    if payload.structured_profile is not None:
        profile.structured_profile = payload.structured_profile
    if payload.name is not None:
        profile.name = payload.name.strip() or None
    if payload.contact_number is not None:
        profile.contact_number = payload.contact_number.strip() or None
    if payload.links is not None:
        raw_links = []
        for link in payload.links:
            if isinstance(link, str):
                raw_links.append(link)
            else:
                raw_links.append(link.model_dump())

        normalized_links = profile_link_service.normalize_links_payload(raw_links)
        profile_link_service.replace_profile_links(
            db=db,
            profile_id=profile.id,
            links=normalized_links,
        )
        profile.links = profile_link_service.normalize_links_for_legacy_column(normalized_links)
    if payload.headline is not None:
        profile.headline = payload.headline
    if payload.summary is not None:
        profile.summary = payload.summary

    # Keep JSON profile aligned with persistent resume identity fields.
    if isinstance(profile.structured_profile, dict):
        if payload.name is not None:
            profile.structured_profile["name"] = profile.name or ""
        if payload.contact_number is not None:
            profile.structured_profile["contact_number"] = profile.contact_number or ""
        if payload.links is not None:
            profile.structured_profile["links"] = profile.links or []

    db.commit()
    db.refresh(profile)

    # Ensure response includes normalized link rows for clients that need typed links.
    profile.profile_links = profile_link_service.get_profile_links(db=db, profile_id=profile.id)
    return profile
