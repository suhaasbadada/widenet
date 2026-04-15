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


# ---------------------------------------------------------------------------
# Resume parsing
# ---------------------------------------------------------------------------

_RESUME_PARSE_SYSTEM = """
You are a resume parser. Extract structured information from the provided resume text.

Return ONLY a JSON object with exactly these fields:
{
  "headline": "<one-line professional title, e.g. Senior Backend Engineer>",
  "summary": "<2-3 sentence professional summary>",
  "skills": ["skill1", "skill2"],
  "experience": [
    {
      "title": "<job title>",
      "company": "<company name>",
      "duration": "<e.g. Jan 2021 - Mar 2023>",
      "description": "<brief description of responsibilities and impact>"
    }
  ]
}

Rules:
- Do not invent information not present in the resume.
- Use plain professional language. No emojis or symbols.
- skills must be a flat list of strings.
- experience must be ordered most-recent first.
""".strip()


def parse_resume(raw_resume: str) -> dict[str, Any]:
    """Convert raw resume text into a structured profile dict.

    Args:
        raw_resume: Plain text extracted from the uploaded resume file.

    Returns:
        Dict with keys: headline, summary, skills, experience.
    """
    return _chat(
        system_prompt=_RESUME_PARSE_SYSTEM,
        user_content=f"Resume text:\n\n{raw_resume}",
    )


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
