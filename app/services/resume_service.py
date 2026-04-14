import uuid

from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.user import User
from app.services import ai_service, storage_service
from app.utils.file_parser import extract_text


class UserNotFoundError(LookupError):
    """Raised when a resume upload references a user that does not exist."""


def process_resume_upload(
    db: Session,
    file_bytes: bytes,
    content_type: str,
    user_id: uuid.UUID,
) -> Profile:
    """Orchestrate the full resume upload pipeline.

    Steps:
    1. Upload file to Supabase Storage and get public URL.
    2. Extract plain text from the file (PDF or DOCX).
    3. Send text to AI for structured parsing.
    4. Persist the resulting profile to the database.

    Raises ValueError (from file_parser or storage_service) for unsupported
    file types, which the route layer maps to a 400 response.
    """
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User '{user_id}' does not exist.")

    resume_url = storage_service.upload_resume(
        file_bytes=file_bytes,
        content_type=content_type,
        user_id=str(user_id),
    )

    raw_resume = extract_text(file_bytes=file_bytes, content_type=content_type)

    # AI parse returns: headline, summary, skills, experience
    parsed = ai_service.parse_resume(raw_resume=raw_resume)

    profile = Profile(
        user_id=user_id,
        resume_url=resume_url,
        raw_resume=raw_resume,
        structured_profile=parsed,
        headline=parsed.get("headline"),
        summary=parsed.get("summary"),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile
