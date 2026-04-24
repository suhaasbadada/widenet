import uuid
import json
import logging
import re
import tempfile
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.resume_schema import (
    ExistingResumeResponse,
    ResumeLink,
    ResumeGenerateResponse,
    ResumeProfileOverrides,
    ResumeRenderPayload,
)
from app.models.user import User
from app.services import ai_service, profile_link_service, resume_render_service, storage_service
from app.utils.file_parser import extract_text


class UserNotFoundError(LookupError):
    """Raised when a resume upload references a user that does not exist."""


class ProfileNotFoundError(LookupError):
    """Raised when a user has no stored profile for resume tailoring."""


class ResumeGenerationValidationError(ValueError):
    """Raised when resume generation input or output violates schema constraints."""


class ResumeGenerationFailedError(RuntimeError):
    """Raised when resume generation cannot produce valid output after retries."""


@dataclass
class GeneratedResumeFileArtifact:
    output_path: str
    media_type: str
    download_name: str
    temp_dir: tempfile.TemporaryDirectory[str]


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


def _extract_links_from_profile(base_resume: dict[str, Any]) -> list[str]:
    raw_links = base_resume.get("links")
    if isinstance(raw_links, list):
        return [profile_link_service.normalize_link_url(str(link)) for link in raw_links if str(link).strip()]

    if isinstance(raw_links, dict):
        collected: list[str] = []
        for value in raw_links.values():
            text = profile_link_service.normalize_link_url(str(value))
            if text:
                collected.append(text)
        return collected

    contact = base_resume.get("contact")
    if isinstance(contact, dict):
        collected = []
        for key in ("linkedin", "github", "portfolio", "website"):
            value = profile_link_service.normalize_link_url(str(contact.get(key, "")))
            if value:
                collected.append(value)
        return collected

    return []


def _extract_name_from_raw_resume(raw_resume: str) -> str:
    for line in raw_resume.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if len(candidate) > 80:
            continue
        if any(token in candidate.lower() for token in ("summary", "experience", "skills", "education")):
            continue
        if "@" in candidate:
            continue
        if sum(char.isdigit() for char in candidate) > 2:
            continue
        return candidate
    return ""


def _extract_contact_from_raw_resume(raw_resume: str) -> str:
    phone_pattern = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
    match = phone_pattern.search(raw_resume)
    return match.group(0).strip() if match else ""


def _extract_links_from_raw_resume(raw_resume: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()

    email_pattern = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
    url_pattern = re.compile(r'https?://[^\s|)"]+')
    bare_url_pattern = re.compile(
        r'(?<!@)\b(?:www\.)?[A-Za-z0-9.-]+\.(?:com|org|net|dev|io|ai|me|co|edu)(?:/[^\s|)"]*)?',
        re.IGNORECASE,
    )

    for match in email_pattern.findall(raw_resume):
        normalized = profile_link_service.normalize_link_url(match)
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            links.append(normalized)

    for match in url_pattern.findall(raw_resume):
        normalized = profile_link_service.normalize_link_url(match)
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            links.append(normalized)

    for match in bare_url_pattern.findall(raw_resume):
        normalized = profile_link_service.normalize_link_url(match)
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            links.append(normalized)

    return links


def _education_section_lines(raw_resume: str) -> list[str]:
    lines = [line.strip() for line in raw_resume.splitlines()]
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.lower() == "education":
            start_index = index + 1
            break

    if start_index is None:
        return []

    collected: list[str] = []
    next_section_tokens = {
        "experience",
        "projects",
        "skills",
        "summary",
        "certifications",
        "awards",
        "publications",
    }
    for line in lines[start_index:]:
        if not line:
            continue
        if line.lower() in next_section_tokens:
            break
        collected.append(line)
    return collected


def _extract_gpa_value(text: str) -> str:
    match = re.search(r"\b(?:GPA|CGPA)\s*:?\s*([^|]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _extract_date_range(text: str) -> tuple[str, str]:
    match = re.search(r"(\d{2}/\d{4})\s*[–-]\s*(Present|\d{2}/\d{4})", text)
    if not match:
        return "", ""
    return match.group(1).strip(), match.group(2).strip()


def _enrich_education_from_raw_resume(education: Any, raw_resume: str) -> list[dict[str, Any]]:
    if not isinstance(education, list):
        return []

    section_lines = _education_section_lines(raw_resume)
    if not section_lines:
        return [item for item in education if isinstance(item, dict)]

    enriched: list[dict[str, Any]] = []
    for item in education:
        if not isinstance(item, dict):
            continue

        updated = dict(item)
        lookup_tokens = [
            str(updated.get("institution") or "").strip(),
            str(updated.get("degree") or "").strip(),
        ]
        matching_index: int | None = None
        for index, line in enumerate(section_lines):
            lowered_line = line.lower()
            if any(token and token.lower() in lowered_line for token in lookup_tokens):
                matching_index = index
                break

        if matching_index is None:
            enriched.append(updated)
            continue

        context = " | ".join(section_lines[matching_index:matching_index + 3])
        institution_line = section_lines[matching_index]
        institution = str(updated.get("institution") or "").strip()
        if institution and institution_line.startswith(institution):
            location = institution_line[len(institution):].strip(" ,|")
            if location and not str(updated.get("location") or "").strip():
                updated["location"] = location

        if not str(updated.get("gpa") or "").strip():
            updated["gpa"] = _extract_gpa_value(context)

        from_value, to_value = _extract_date_range(context)
        if from_value and not str(updated.get("from") or "").strip():
            updated["from"] = from_value
        if to_value and not str(updated.get("to") or "").strip():
            updated["to"] = to_value

        enriched.append(updated)

    return enriched


def _extract_name_from_profile(base_resume: dict[str, Any]) -> str:
    return (
        str(base_resume.get("name") or "").strip()
        or str(base_resume.get("full_name") or "").strip()
        or str(base_resume.get("candidate_name") or "").strip()
    )


def _extract_contact_from_profile(base_resume: dict[str, Any]) -> str:
    return (
        str(base_resume.get("contact_number") or "").strip()
        or str(base_resume.get("phone") or "").strip()
    )


def _normalized_output_file_name(output_format: str, file_name: str | None) -> str:
    extension = ".docx" if output_format == "docx" else ".pdf"
    default_name = f"resume{extension}"
    normalized = (file_name or default_name).strip() or default_name
    if not normalized.lower().endswith(extension):
        normalized = f"{normalized}{extension}"
    return normalized


def _ensure_render_required_shape(
    base_resume: dict[str, Any],
    profile_overrides: ResumeProfileOverrides | None,
) -> dict[str, Any]:
    profile_overrides = profile_overrides or ResumeProfileOverrides()

    fallback_name = _extract_name_from_profile(base_resume)
    fallback_contact_number = _extract_contact_from_profile(base_resume)

    normalized = dict(base_resume)
    normalized["name"] = (profile_overrides.name or fallback_name).strip()
    normalized["contact_number"] = (
        profile_overrides.contact_number or fallback_contact_number
    ).strip()
    normalized["links"] = profile_overrides.links or _extract_links_from_profile(base_resume)

    base_summary = str(base_resume.get("summary") or "").strip()
    normalized["summary"] = (profile_overrides.summary or base_summary).strip()

    if profile_overrides.skills is not None:
        normalized["skills"] = profile_overrides.skills
    else:
        normalized["skills"] = base_resume.get("skills") or {}

    normalized["experience"] = (
        profile_overrides.experience
        if profile_overrides.experience is not None
        else (base_resume.get("experience") or [])
    )
    normalized["projects"] = (
        profile_overrides.projects
        if profile_overrides.projects is not None
        else (base_resume.get("projects") or [])
    )
    normalized["education"] = (
        profile_overrides.education
        if profile_overrides.education is not None
        else (base_resume.get("education") or [])
    )
    return normalized


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
    template_path: str = "app/resume-templates/Template1.docx",
    docx_file_name: str = "resume.docx",
    pdf_file_name: str = "resume.pdf",
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

            return ResumeGenerateResponse(
                tailored_resume=normalized,
                resume_json=normalized,
                render_docx_payload=ResumeRenderPayload(
                    resume_json=normalized,
                    template_path=template_path,
                    file_name=docx_file_name,
                ),
                render_pdf_payload=ResumeRenderPayload(
                    resume_json=normalized,
                    template_path=template_path,
                    file_name=pdf_file_name,
                ),
            )
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
    profile_overrides: ResumeProfileOverrides | None = None,
    template_path: str = "app/resume-templates/Template1.docx",
    docx_file_name: str = "resume.docx",
    pdf_file_name: str = "resume.pdf",
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
    if profile.name and "name" not in base_resume:
        base_resume["name"] = profile.name
    if profile.contact_number and "contact_number" not in base_resume:
        base_resume["contact_number"] = profile.contact_number
    link_urls = profile_link_service.get_profile_link_urls(db=db, profile_id=profile.id)
    if not link_urls and profile.links:
        normalized_links = profile_link_service.normalize_links_payload(profile.links)
        profile_link_service.replace_profile_links(
            db=db,
            profile_id=profile.id,
            links=normalized_links,
        )
        db.commit()
        link_urls = profile_link_service.get_profile_link_urls(db=db, profile_id=profile.id)
    if link_urls and "links" not in base_resume:
        base_resume["links"] = link_urls
    elif profile.links and "links" not in base_resume:
        base_resume["links"] = profile.links
    render_ready_resume = _ensure_render_required_shape(base_resume, profile_overrides)

    return generate_tailored_resume(
        job_description=job_description,
        base_resume=render_ready_resume,
        template_path=template_path,
        docx_file_name=docx_file_name,
        pdf_file_name=pdf_file_name,
        max_retries=max_retries,
    )


def generate_and_render_resume_from_registered_profile(
    db: Session,
    user_id: uuid.UUID,
    job_description: str,
    output_format: str,
    file_name: str | None = None,
    profile_overrides: ResumeProfileOverrides | None = None,
    template_path: str = "app/resume-templates/Template1.docx",
    docx_file_name: str = "resume.docx",
    pdf_file_name: str = "resume.pdf",
    max_retries: int = 3,
) -> GeneratedResumeFileArtifact:
    """Generate a tailored resume and immediately render it as DOCX/PDF."""
    generation_response = generate_tailored_resume_from_registered_profile(
        db=db,
        user_id=user_id,
        job_description=job_description,
        profile_overrides=profile_overrides,
        template_path=template_path,
        docx_file_name=docx_file_name,
        pdf_file_name=pdf_file_name,
        max_retries=max_retries,
    )

    if output_format == "docx":
        resolved_name = _normalized_output_file_name("docx", file_name or docx_file_name)
        artifact = resume_render_service.render_resume_to_docx(
            resume_json=generation_response.resume_json,
            template_path=template_path,
            file_name=resolved_name,
        )
        return GeneratedResumeFileArtifact(
            output_path=artifact.docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            download_name=resolved_name,
            temp_dir=artifact.temp_dir,
        )

    resolved_name = _normalized_output_file_name("pdf", file_name or pdf_file_name)
    artifact = resume_render_service.render_resume_to_pdf(
        resume_json=generation_response.resume_json,
        template_path=template_path,
        file_name=resolved_name,
    )
    return GeneratedResumeFileArtifact(
        output_path=artifact.pdf_path,
        media_type="application/pdf",
        download_name=resolved_name,
        temp_dir=artifact.temp_dir,
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

    typed_links = profile_link_service.get_profile_links(db=db, profile_id=profile.id)
    if not typed_links and profile.links:
        normalized_links = profile_link_service.normalize_links_payload(profile.links)
        profile_link_service.replace_profile_links(
            db=db,
            profile_id=profile.id,
            links=normalized_links,
        )
        db.commit()
        typed_links = profile_link_service.get_profile_links(db=db, profile_id=profile.id)
    link_urls = [link.url for link in typed_links]
    links = link_urls or profile.links

    return ExistingResumeResponse(
        resume_url=profile.resume_url,
        raw_resume=profile.raw_resume,
        structured_profile=profile.structured_profile or {
            "headline": profile.headline or "",
            "summary": profile.summary or "",
            "skills": [],
            "experience": [],
        },
        name=profile.name,
        contact_number=profile.contact_number,
        links=links,
        profile_links=[
            ResumeLink(type=link.link_type, url=link.url, is_primary=link.is_primary)
            for link in typed_links
        ]
        if typed_links
        else None,
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

    profile = Profile(
        user_id=user_id,
        resume_url=resume_url,
        raw_resume=raw_resume,
        structured_profile=parsed,
        name=parsed_name or None,
        contact_number=parsed_contact or None,
        links=parsed.get("links") or parsed_links,
        headline=parsed.get("headline"),
        summary=parsed.get("summary"),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    normalized_links = profile_link_service.normalize_links_payload(profile.links or [])
    profile_link_service.replace_profile_links(
        db=db,
        profile_id=profile.id,
        links=normalized_links,
    )
    profile.links = profile_link_service.normalize_links_for_legacy_column(normalized_links)
    db.commit()
    db.refresh(profile)
    profile.profile_links = profile_link_service.get_profile_links(db=db, profile_id=profile.id)

    pruned = _prune_old_profiles(db=db, user_id=user_id, max_profiles=5)
    if pruned:
        _logger.info("Pruned %s old profile(s) for user %s after resume upload.", pruned, user_id)

    return profile


def _prune_old_profiles(db: Session, user_id: uuid.UUID, max_profiles: int) -> int:
    """Keep only the most recent N profile rows for a user."""
    stale_profiles = db.scalars(
        select(Profile)
        .where(Profile.user_id == user_id)
        .order_by(Profile.created_at.desc(), Profile.id.desc())
        .offset(max_profiles)
    ).all()

    if not stale_profiles:
        return 0

    for stale_profile in stale_profiles:
        db.delete(stale_profile)

    db.commit()
    return len(stale_profiles)
