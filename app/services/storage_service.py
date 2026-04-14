import os
import uuid
from urllib.parse import quote

import requests

_SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
_SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# Bucket must exist in Supabase Storage and be configured as public
# so that the returned URL is directly accessible without auth headers.
_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "resumes").split("#", 1)[0].strip()


def upload_resume(file_bytes: bytes, content_type: str, user_id: str) -> str:
    """Upload a resume file to Supabase Storage and return its public URL.

    Each upload gets a UUID-based path to prevent collisions when a user
    re-uploads. Format: {user_id}/{uuid}.{ext}
    """
    ext = _extension_for(content_type)
    file_path = f"{user_id}/{uuid.uuid4()}.{ext}"
    upload_url = f"{_SUPABASE_URL}/storage/v1/object/{_BUCKET}/{quote(file_path, safe='/')}"
    headers = {
        "Authorization": f"Bearer {_SUPABASE_SERVICE_KEY}",
        "apikey": _SUPABASE_SERVICE_KEY,
        "Content-Type": content_type,
        "x-upsert": "false",
    }

    response = requests.post(upload_url, headers=headers, data=file_bytes, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        error_text = response.text.strip() or response.reason
        raise ValueError(f"Failed to upload resume to Supabase Storage: {error_text}") from exc

    return _public_url_for(file_path)


def _public_url_for(file_path: str) -> str:
    """Construct the public URL for an object stored in a public bucket."""
    encoded_path = quote(file_path, safe="/")
    return f"{_SUPABASE_URL}/storage/v1/object/public/{_BUCKET}/{encoded_path}"


def _extension_for(content_type: str) -> str:
    """Map MIME type to a file extension for storage path construction."""
    mapping = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc",
    }
    ext = mapping.get(content_type)
    if ext is None:
        raise ValueError(f"Unsupported content type for storage: {content_type}")
    return ext
