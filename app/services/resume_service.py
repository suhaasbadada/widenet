import uuid
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.resume_schema import ExistingResumeResponse, ResumeGenerateResponse
from app.models.user import User
from app.services import ai_service, storage_service
from app.utils.file_parser import extract_text


class UserNotFoundError(LookupError):
    """Raised when a resume upload references a user that does not exist."""


class ProfileNotFoundError(LookupError):
    """Raised when a user has no stored profile for resume tailoring."""


class ResumeGenerationValidationError(ValueError):
    """Raised when resume generation input or output violates schema constraints."""


class ResumeGenerationFailedError(RuntimeError):
    """Raised when resume generation cannot produce valid output after retries."""


_logger = logging.getLogger(__name__)

_RESUME_TRANSFORM_SYSTEM_PROMPT = """You are a resume transformation engine.

Your job:
- Tailor a resume JSON to a given job description
- Keep the JSON schema EXACTLY the same
- Do not add, remove, or rename any keys
- Only modify values
- Write the resume to be as technically unrejectable as possible for ATS screening and hiring-manager review

Rules:
- Return ONLY valid JSON (no explanations, no extra text)
- Do not change schema structure
- Do not invent companies, roles, or metrics
- Rewrite bullets to match job description keywords
- Prioritize relevant experience
- Maximize ATS keyword alignment, clarity, and evidence of fit without keyword stuffing
- Make every line skimmable, concrete, and compelling to a hiring manager
- Keep bullets concise, impact-focused, and realistic
- If unsure, retain original content
- If any field is missing in output, copy it exactly from input JSON"""

_RETRY_SUFFIX = (
    "Your previous output was invalid JSON or violated schema. "
    "Fix formatting only. Do not change content."
)

_UNCHANGED_SUFFIX = (
    "Your previous output was valid but effectively unchanged from the input resume. "
    "Now tailor values more strongly to the JD while staying truthful: "
    "rewrite summary and bullets for relevance, prioritize matching experience, "
    "and keep the exact same schema."
)


def _build_user_prompt(
    job_description: str,
    base_resume_json: str,
    retry_reason: str | None,
) -> str:
    prompt = (
        "JOB DESCRIPTION:\n"
        f"{job_description}\n\n"
        "BASE RESUME JSON:\n"
        f"{base_resume_json}\n\n"
        "TASK:\n"
        "Return a modified JSON tailored for this job.\n"
        "Return JSON only."
    )
    if retry_reason == "invalid":
        prompt = f"{prompt}\n\n{_RETRY_SUFFIX}"
    elif retry_reason == "unchanged":
        prompt = f"{prompt}\n\n{_UNCHANGED_SUFFIX}"
    return prompt


def _validate_input_resume(base_resume: Any) -> dict[str, Any]:
    if not isinstance(base_resume, dict):
        raise ResumeGenerationValidationError("Field 'base_resume' must be a JSON object.")
    if not base_resume:
        raise ResumeGenerationValidationError("Field 'base_resume' cannot be empty.")
    return base_resume


def _validate_exact_schema(base: Any, candidate: Any, path: str = "root") -> None:
    if isinstance(base, dict):
        if not isinstance(candidate, dict):
            raise ResumeGenerationValidationError(f"Type mismatch at {path}: expected object.")

        base_keys = list(base.keys())
        candidate_keys = list(candidate.keys())

        missing = [k for k in base_keys if k not in candidate]
        extra = [k for k in candidate_keys if k not in base]
        if missing or extra:
            raise ResumeGenerationValidationError(
                f"Schema mismatch at {path}: missing keys={missing}, extra keys={extra}."
            )

        for key in base_keys:
            _validate_exact_schema(base[key], candidate[key], f"{path}.{key}")
        return

    if isinstance(base, list):
        if not isinstance(candidate, list):
            raise ResumeGenerationValidationError(f"Type mismatch at {path}: expected list.")

        if not base:
            return

        template = base[0]
        for idx, item in enumerate(candidate):
            _validate_exact_schema(template, item, f"{path}[{idx}]")
        return

    if base is None:
        return

    if not isinstance(candidate, type(base)):
        raise ResumeGenerationValidationError(
            f"Type mismatch at {path}: expected {type(base).__name__}, got {type(candidate).__name__}."
        )


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def _normalize_to_schema(base: Any, candidate: Any, path: str = "root") -> Any:
    if isinstance(base, dict):
        result: dict[str, Any] = {}
        for key, base_value in base.items():
            candidate_value = candidate.get(key) if isinstance(candidate, dict) else None
            result[key] = _normalize_to_schema(base_value, candidate_value, f"{path}.{key}")
        return result

    if isinstance(base, list):
        if not isinstance(candidate, list):
            return []

        if not base:
            normalized_list = ["" if item is None else item for item in candidate]
        else:
            template = base[0]
            normalized_list = [
                _normalize_to_schema(template, item, f"{path}[]") for item in candidate
            ]

        path_lower = path.lower()
        if "bullet" in path_lower:
            bullet_items = [str(item).strip() for item in normalized_list if str(item).strip()]
            bullet_items = [item[:180].strip() for item in bullet_items]
            bullet_items = _dedupe_preserve_order(bullet_items)
            return bullet_items[:4]

        return normalized_list

    if candidate is None:
        if isinstance(base, list):
            return []
        if isinstance(base, dict):
            return {}
        if isinstance(base, bool):
            return base
        if isinstance(base, (int, float)):
            return base
        return ""

    if isinstance(base, str):
        return str(candidate)
    if isinstance(base, bool):
        return bool(candidate)
    if isinstance(base, int) and not isinstance(base, bool):
        return int(candidate)
    if isinstance(base, float):
        return float(candidate)

    return candidate


def _extract_json_candidate(raw: str) -> str:
    """Extract a JSON object from raw LLM text, tolerating code fences or prefixes."""
    text = (raw or "").strip()
    if not text:
        raise ResumeGenerationValidationError("LLM returned an empty response.")

    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    raise ResumeGenerationValidationError("LLM response did not contain a JSON object.")


def _parse_llm_json(raw: str) -> dict[str, Any]:
    candidate = _extract_json_candidate(raw)
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ResumeGenerationValidationError("LLM response JSON root must be an object.")
    return parsed


def _is_effectively_unchanged(base_resume: dict[str, Any], candidate_resume: dict[str, Any]) -> bool:
    """Return True when candidate values are effectively identical to the base resume."""
    return json.dumps(base_resume, sort_keys=True) == json.dumps(candidate_resume, sort_keys=True)


def generate_tailored_resume(
    job_description: str,
    base_resume: dict[str, Any],
    max_retries: int = 3,
) -> ResumeGenerateResponse:
    """Generate a job-tailored resume while preserving the exact base resume schema."""
    if not isinstance(job_description, str) or len(job_description.strip()) < 20:
        raise ResumeGenerationValidationError(
            "Field 'job_description' must be a non-empty string with at least 20 characters."
        )

    validated_base_resume = _validate_input_resume(base_resume)
    base_resume_json = json.dumps(validated_base_resume, ensure_ascii=True)

    last_error: Exception | None = None
    retry_reason: str | None = None

    for attempt in range(1, max_retries + 1):
        user_prompt = _build_user_prompt(
            job_description=job_description.strip(),
            base_resume_json=base_resume_json,
            retry_reason=retry_reason,
        )

        try:
            llm_raw = ai_service.generate_llm_response(
                system_prompt=_RESUME_TRANSFORM_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            parsed = _parse_llm_json(llm_raw)
            _validate_exact_schema(validated_base_resume, parsed)
            normalized = _normalize_to_schema(validated_base_resume, parsed)
            _validate_exact_schema(validated_base_resume, normalized)

            if _is_effectively_unchanged(validated_base_resume, normalized) and attempt < max_retries:
                last_error = ResumeGenerationValidationError(
                    "Model output was unchanged from the stored resume."
                )
                retry_reason = "unchanged"
                _logger.info(
                    "Resume generation returned unchanged output on attempt %s/%s; retrying with stronger tailoring guidance.",
                    attempt,
                    max_retries,
                )
                continue

            return ResumeGenerateResponse(tailored_resume=normalized)
        except (json.JSONDecodeError, ResumeGenerationValidationError, TypeError, ValueError) as exc:
            last_error = exc
            retry_reason = "invalid"
            _logger.warning(
                "Resume generation validation failed on attempt %s/%s: %s",
                attempt,
                max_retries,
                exc,
            )
            continue
        except Exception as exc:  # pragma: no cover - defensive fallback for provider/runtime errors
            last_error = exc
            _logger.exception("Resume generation failed due to LLM/provider error.")
            break

    raise ResumeGenerationFailedError(
        "Failed to generate a schema-valid tailored resume after retries."
    ) from last_error


def generate_tailored_resume_from_registered_profile(
    db: Session,
    user_id: uuid.UUID,
    job_description: str,
    max_retries: int = 3,
) -> ResumeGenerateResponse:
    """Generate a tailored resume from the caller's latest stored profile JSON."""
    profile = db.scalar(
        select(Profile)
        .where(Profile.user_id == user_id)
        .order_by(Profile.created_at.desc())
    )
    if profile is None:
        raise ProfileNotFoundError(
            "No profile found for this user. Upload a resume before generating a tailored resume."
        )

    base_resume = profile.structured_profile or {
        "headline": profile.headline or "",
        "summary": profile.summary or "",
        "skills": [],
        "experience": [],
    }

    return generate_tailored_resume(
        job_description=job_description,
        base_resume=base_resume,
        max_retries=max_retries,
    )


def get_existing_resume_for_user(db: Session, user_id: uuid.UUID) -> ExistingResumeResponse:
    """Return the latest uploaded resume/profile data for a user."""
    profile = db.scalar(
        select(Profile)
        .where(Profile.user_id == user_id)
        .order_by(Profile.created_at.desc())
    )
    if profile is None:
        raise ProfileNotFoundError(
            "No profile found for this user. Upload a resume before fetching it."
        )

    return ExistingResumeResponse(
        resume_url=profile.resume_url,
        raw_resume=profile.raw_resume,
        structured_profile=profile.structured_profile or {
            "headline": profile.headline or "",
            "summary": profile.summary or "",
            "skills": [],
            "experience": [],
        },
        headline=profile.headline,
        summary=profile.summary,
    )


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
