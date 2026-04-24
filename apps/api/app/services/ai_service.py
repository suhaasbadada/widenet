import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def _groq_base_url() -> str | None:
    """Normalize Groq base URL overrides to avoid duplicated path segments."""
    base_url = os.environ.get("GROQ_BASE_URL")
    if not base_url:
        return None

    normalized = base_url.rstrip("/")

    # Legacy OpenAI-compatible values sometimes include /openai/v1, but the
    # native Groq SDK appends its own API path. Strip it to avoid 404s like
    # /openai/v1/openai/v1/chat/completions.
    for suffix in ("/openai/v1", "/openai"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break

    return normalized


# Use the native Groq client to avoid coupling runtime setup to the OpenAI SDK.
_client = Groq(api_key=os.environ["GROQ_API"], base_url=_groq_base_url())

_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _chat(system_prompt: str, user_content: str) -> dict[str, Any]:
    """Send a Groq chat completion request and return parsed JSON.

    json_object response format guarantees the model returns valid JSON, which
    lets us skip defensive regex extraction and go straight to json.loads().
    """
    response = _client.chat.completions.create(
        model=_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,  # low temperature for consistent, structured output
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


def generate_llm_response(system_prompt: str, user_prompt: str) -> str:
    """Generate raw LLM text content for workflows that handle parsing/validation externally."""
    response = _client.chat.completions.create(
        model=_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return (response.choices[0].message.content or "").strip()


# ---------------------------------------------------------------------------
# Resume parsing
# ---------------------------------------------------------------------------

_RESUME_PARSE_SYSTEM = """
You are a resume parser. Extract structured information from the provided resume text.

Return ONLY a JSON object with at least these top-level fields:
{
    "name": "<candidate full name>",
    "contact_number": "<primary phone number>",
    "links": ["<email/linkedin/github/portfolio URLs or email strings>"],
  "headline": "<one-line professional title, e.g. Senior Backend Engineer>",
  "summary": "<2-3 sentence professional summary>",
  "skills": {
    "<category_name>": ["skill1", "skill2"]
  },
  "experience": [
    {
      "title": "<job title>",
      "company": "<company name>",
      "duration": "<e.g. Jan 2021 - Mar 2023>",
      "location": "<optional>",
      "points": ["bullet 1", "bullet 2"]
    }
    ],
    "projects": [
        {
            "name": "<project name>",
            "description": "<optional short summary>",
            "technologies": ["tech1", "tech2"],
            "points": ["bullet 1", "bullet 2"]
        }
    ],
    "education": [
        {
            "institution": "<school or university>",
            "degree": "<degree>",
            "major": "<major or specialization>",
            "location": "<optional>",
            "gpa": "<GPA if present>",
            "from": "<start date if present>",
            "to": "<end date if present>"
        }
  ]
}

Rules:
- Do not invent information not present in the resume.
- Extract email addresses and public profile URLs into links.
- Preserve the candidate name exactly as written near the top of the resume.
- Extract the best phone number into contact_number.
- Use plain professional language. No emojis or symbols.
- Preserve skill subcategories from the resume whenever possible (frontend, backend, languages, databases, cloud, tools, frameworks, etc.).
- Do NOT collapse all skills into one flat list.
- experience must be ordered most-recent first.
- Preserve all meaningful bullet points for each experience entry in points[]; do not keep only one point.
- If the resume has additional sections (projects, education, certifications, awards, publications, volunteering), include them with structured fields.
- For education, extract GPA and date range whenever present instead of leaving them out.
- For public links without a scheme, keep the visible value but preserve the full domain/path.
""".strip()


def _to_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    return []


def _normalize_skills(skills: Any) -> dict[str, list[str]]:
    if isinstance(skills, dict):
        normalized: dict[str, list[str]] = {}
        for key, value in skills.items():
            key_name = str(key).strip() or "general"
            normalized[key_name] = _to_string_list(value)
        return normalized
    return {"general": _to_string_list(skills)}


def _normalize_experience(experience: Any) -> list[dict[str, Any]]:
    if not isinstance(experience, list):
        return []

    normalized_items: list[dict[str, Any]] = []
    for item in experience:
        if not isinstance(item, dict):
            continue
        points = _to_string_list(item.get("points"))
        if not points:
            points = _to_string_list(item.get("bullets"))
        if not points:
            points = _to_string_list(item.get("responsibilities"))
        if not points:
            points = _to_string_list(item.get("description"))

        normalized_items.append(
            {
                "title": str(item.get("title", "")).strip(),
                "company": str(item.get("company", "")).strip(),
                "duration": str(item.get("duration", "")).strip(),
                "location": str(item.get("location", "")).strip(),
                "points": points,
            }
        )

    return normalized_items


def _normalize_projects(projects: Any) -> list[dict[str, Any]]:
    if not isinstance(projects, list):
        return []

    normalized_items: list[dict[str, Any]] = []
    for item in projects:
        if not isinstance(item, dict):
            continue
        normalized_items.append(
            {
                "name": str(item.get("name", "")).strip() or str(item.get("title", "")).strip(),
                "description": str(item.get("description", "")).strip() or str(item.get("summary", "")).strip(),
                "technologies": _to_string_list(item.get("technologies") or item.get("tech") or item.get("stack")),
                "points": _to_string_list(item.get("points") or item.get("bullets") or item.get("impact")),
            }
        )
    return normalized_items


def _normalize_education(education: Any) -> list[dict[str, Any]]:
    if not isinstance(education, list):
        return []

    normalized_items: list[dict[str, Any]] = []
    for item in education:
        if not isinstance(item, dict):
            continue

        degree_value = str(item.get("degree", "")).strip()
        major_value = str(item.get("major", "")).strip() or str(item.get("field", "")).strip()
        split_parts = degree_value.rsplit(" in ", 1)
        if len(split_parts) == 2 and split_parts[1].strip():
            suffix = split_parts[1].strip()
            if not major_value or suffix.lower() == major_value.lower():
                degree_value = split_parts[0].strip()
                major_value = major_value or suffix

        lowered_degree = degree_value.lower()
        if any(token in lowered_degree for token in ("master", "m.s", "msc", "m.tech", "mba", "m.e")):
            degree_value = "Masters"
        elif any(token in lowered_degree for token in ("bachelor", "b.s", "bsc", "b.tech", "b.e", "ba ")):
            degree_value = "Bachelors"
        elif any(token in lowered_degree for token in ("phd", "doctor", "d.phil")):
            degree_value = "PhD"

        normalized_items.append(
            {
                "institution": str(item.get("institution", "")).strip() or str(item.get("school", "")).strip() or str(item.get("university", "")).strip(),
                "degree": degree_value,
                "major": major_value,
                "gpa": str(item.get("gpa", "")).strip() or str(item.get("cgpa", "")).strip(),
                "from": str(item.get("from", "")).strip() or str(item.get("start", "")).strip(),
                "to": str(item.get("to", "")).strip() or str(item.get("end", "")).strip() or str(item.get("year", "")).strip(),
                "location": str(item.get("location", "")).strip(),
            }
        )

        if not normalized_items[-1]["from"] or not normalized_items[-1]["to"]:
            duration = str(item.get("duration", "")).strip() or str(item.get("date_range", "")).strip()
            if duration:
                parts = [part.strip() for part in duration.replace("—", "-").replace("–", "-").split("-") if part.strip()]
                if len(parts) >= 2:
                    normalized_items[-1]["from"] = normalized_items[-1]["from"] or parts[0]
                    normalized_items[-1]["to"] = normalized_items[-1]["to"] or parts[1]
    return normalized_items


def _normalize_parsed_resume(parsed: Any) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        return {
            "name": "",
            "contact_number": "",
            "links": [],
            "headline": "",
            "summary": "",
            "skills": {"general": []},
            "experience": [],
            "projects": [],
            "education": [],
        }

    normalized: dict[str, Any] = {
        "name": str(parsed.get("name", "")).strip() or str(parsed.get("full_name", "")).strip(),
        "contact_number": str(parsed.get("contact_number", "")).strip() or str(parsed.get("phone", "")).strip(),
        "links": _to_string_list(parsed.get("links", [])),
        "headline": str(parsed.get("headline", "")).strip(),
        "summary": str(parsed.get("summary", "")).strip(),
        "skills": _normalize_skills(parsed.get("skills", {})),
        "experience": _normalize_experience(parsed.get("experience", [])),
        "projects": _normalize_projects(parsed.get("projects", [])),
        "education": _normalize_education(parsed.get("education", [])),
    }

    # Preserve additional top-level sections from the resume without flattening.
    for key, value in parsed.items():
        if key in normalized:
            continue
        normalized[key] = value

    return normalized


def parse_resume(raw_resume: str) -> dict[str, Any]:
    """Convert raw resume text into a structured profile dict.

    Args:
        raw_resume: Plain text extracted from the uploaded resume file.

    Returns:
        Dict with keys: headline, summary, skills, experience.
    """
    parsed = _chat(
        system_prompt=_RESUME_PARSE_SYSTEM,
        user_content=f"Resume text:\n\n{raw_resume}",
    )
    return _normalize_parsed_resume(parsed)


# ---------------------------------------------------------------------------
# Job application answer generation
# ---------------------------------------------------------------------------

_ANSWER_SYSTEM = """
You are an expert career coach helping a candidate answer job application questions.

Return ONLY a JSON object with exactly this field:
{
  "answer": "<tailored answer to the question>"
}

Rules:
- Answer must be specific and relevant to the job and candidate profile.
- Keep the answer concise and professional (150-250 words unless question demands more).
- No emojis, hyphens as bullets, or decorative formatting.
- Write in first person from the candidate's perspective.
""".strip()


def generate_answer(
    profile: dict[str, Any],
    job_title: str,
    job_description: str,
    question: str,
) -> dict[str, Any]:
    """Generate a tailored answer to a job application question.

    Args:
        profile:          Structured candidate profile (output of parse_resume).
        job_title:        Title of the role being applied to.
        job_description:  Full job description text.
        question:         The specific application question to answer.

    Returns:
        Dict with key: answer.
    """
    user_content = (
        f"Candidate profile:\n{json.dumps(profile, indent=2)}\n\n"
        f"Job title: {job_title}\n\n"
        f"Job description:\n{job_description}\n\n"
        f"Question: {question}"
    )
    return _chat(system_prompt=_ANSWER_SYSTEM, user_content=user_content)


# ---------------------------------------------------------------------------
# Recruiter outreach generation
# ---------------------------------------------------------------------------

_OUTREACH_SYSTEM = """
You are an expert at writing personalized recruiter outreach messages for job seekers.

Return ONLY a JSON object with exactly these fields:
{
  "subject": "<compelling email subject line>",
  "message": "<full outreach message body>"
}

Rules:
- Subject must be concise, specific, and role-relevant (max 10 words).
- Message must be 3-4 short paragraphs: opening hook, candidate value, specific fit, call to action.
- Keep the total message under 200 words.
- No emojis, no hyphens or dashes as decorative elements, no hollow phrases like "I hope this email finds you well".
- Professional, confident, and direct tone.
- Write in first person from the candidate's perspective.
""".strip()


def generate_outreach(
    profile: dict[str, Any],
    job_title: str,
    company: str,
    job_description: str,
) -> dict[str, Any]:
    """Generate a personalized recruiter outreach message.

    Args:
        profile:          Structured candidate profile (output of parse_resume).
        job_title:        Title of the role the candidate is targeting.
        company:          Company name.
        job_description:  Job description text for context.

    Returns:
        Dict with keys: subject, message.
    """
    user_content = (
        f"Candidate profile:\n{json.dumps(profile, indent=2)}\n\n"
        f"Target role: {job_title} at {company}\n\n"
        f"Job description:\n{job_description}"
    )
    return _chat(system_prompt=_OUTREACH_SYSTEM, user_content=user_content)


# ---------------------------------------------------------------------------
# Cover letter generation
# ---------------------------------------------------------------------------

_COVER_LETTER_SYSTEM = """
You are an expert career writing assistant.

Return ONLY a JSON object with exactly this field:
{
  "cover_letter": "<full cover letter body>"
}

Rules:
- Use the candidate profile and provided job context only.
- Do not invent experience, projects, or skills.
- Keep writing natural and specific to the JD.
- Use 4 paragraphs: intent, relevant experience, proof via projects/impact, close.
- Keep length between 250 and 450 words.
- No bullet points, no headings, no emojis.
""".strip()


def generate_cover_letter(
    profile: dict[str, Any],
    job_title: str,
    company: str,
    job_description: str,
    company_context: str | None = None,
) -> dict[str, Any]:
    """Generate a personalized cover letter from profile + JD context."""
    user_content = (
        f"Candidate profile:\n{json.dumps(profile, indent=2)}\n\n"
        f"Job title: {job_title}\n"
        f"Company: {company}\n\n"
        f"Job description:\n{job_description}\n\n"
        f"Company context:\n{company_context or ''}"
    )
    return _chat(system_prompt=_COVER_LETTER_SYSTEM, user_content=user_content)


# ---------------------------------------------------------------------------
# Job match scoring
# ---------------------------------------------------------------------------

_JOB_MATCH_SYSTEM = """
You are a hiring assistant that scores how well a candidate profile matches a job.

Return ONLY a JSON object with exactly these fields:
{
  "match_score": 0,
  "reasoning": "<short explanation>",
  "skills_matched": ["skill1", "skill2"]
}

Rules:
- match_score must be an integer between 0 and 100.
- reasoning must be concise and specific to the job requirements.
- skills_matched must contain only concrete skills found in both profile and job context.
""".strip()


def score_job_match(
    profile: dict[str, Any],
    job_title: str,
    company: str,
    job_description: str,
) -> dict[str, Any]:
    """Score a profile against a job and return structured matching details."""
    user_content = (
        f"Candidate profile:\n{json.dumps(profile, indent=2)}\n\n"
        f"Target role: {job_title} at {company}\n\n"
        f"Job description:\n{job_description}"
    )
    return _chat(system_prompt=_JOB_MATCH_SYSTEM, user_content=user_content)


# ---------------------------------------------------------------------------
# Job copilot generation
# ---------------------------------------------------------------------------

_COPILOT_SYSTEM = """
You are an AI job application copilot.

Your job is to help users:
- generate job application answers
- write cover letters
- improve resume content
- create cold outreach messages

You always rely on:
- user profile (resume, projects, experience)
- job description (JD)
- company context (if available)

You must always:
- personalize responses based on user background
- align output to job description requirements
- avoid generic or vague writing
- never invent experience or skills not present in user data

When writing:
- be concise, natural, and human-like
- prioritize specificity over filler language
- keep outputs ready to copy-paste

If the task is unclear:
- ask one short clarifying question instead of guessing

Return ONLY a JSON object with exactly this field:
{
  "output": "<final output text>"
}
""".strip()


def generate_job_copilot_output(
    profile: dict[str, Any],
    task: str,
    job_title: str,
    job_description: str,
    company: str | None,
    company_context: str | None,
    question: str | None,
    user_instruction: str | None,
) -> dict[str, Any]:
    """Generate a single final output text for a job-copilot task."""
    user_content = (
        f"Task: {task}\n\n"
        f"Candidate profile:\n{json.dumps(profile, indent=2)}\n\n"
        f"Job title: {job_title}\n"
        f"Company: {company or ''}\n\n"
        f"Job description:\n{job_description}\n\n"
        f"Company context:\n{company_context or ''}\n\n"
        f"Question (for job answer tasks):\n{question or ''}\n\n"
        f"Additional user instruction:\n{user_instruction or ''}\n\n"
        "Task guidance:\n"
        "- task=job_answer: return only the tailored answer text\n"
        "- task=cover_letter: return only the full cover letter body (no headings)\n"
        "- task=resume_improve: return only improved resume bullet/content text\n"
        "- task=cold_outreach: return only the outreach message with a meaningful subject line at the top"
    )
    return _chat(system_prompt=_COPILOT_SYSTEM, user_content=user_content)
