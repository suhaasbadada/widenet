import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.workday_skills import WorkdaySkillsResponse
from app.services import ai_service, job_service


class WorkdaySkillsGenerationError(ValueError):
    """Raised when generated Workday skills are missing or invalid."""


def generate_workday_skills(
    db: Session,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    max_skills: int = 30,
) -> WorkdaySkillsResponse:
    """Generate copy-pasteable Workday skills from a selected job."""
    job = job_service.get_job_by_id(db=db, job_id=job_id, user_id=user_id)

    profile = db.scalar(
        select(Profile)
        .where(Profile.user_id == user_id)
        .order_by(Profile.created_at.desc())
    )
    profile_context = None
    if profile is not None:
        profile_context = profile.structured_profile or {
            "headline": profile.headline,
            "summary": profile.summary,
            "skills": [],
            "experience": [],
        }

    generated = ai_service.generate_workday_skills(
        profile=profile_context,
        job_title=job.title,
        company=job.company,
        job_description=job.description or "",
        max_skills=max_skills,
    )

    normalized = _normalize_skills(generated.get("skills", []), max_skills=max_skills)
    if not normalized:
        raise WorkdaySkillsGenerationError(
            "Could not generate Workday skills from this job description."
        )

    return WorkdaySkillsResponse(
        skills=normalized,
        skills_csv=", ".join(normalized),
    )


def _normalize_skills(raw_skills: object, max_skills: int) -> list[str]:
    if isinstance(raw_skills, str):
        source = [item.strip() for item in raw_skills.split(",")]
    elif isinstance(raw_skills, list):
        source = [str(item).strip() for item in raw_skills]
    else:
        source = []

    deduped: list[str] = []
    seen: set[str] = set()
    for skill in source:
        if not skill:
            continue
        key = skill.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(skill)

    return deduped[:max_skills]
