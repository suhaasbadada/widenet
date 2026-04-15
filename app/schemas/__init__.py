from app.schemas.answer import AnswerGenerateRequest, AnswerGenerateResponse
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, AuthResponse
from app.schemas.generated_content import GeneratedContentCreate, GeneratedContentResponse
from app.schemas.job import JobCreate, JobResponse
from app.schemas.job_match import JobMatchItem, JobMatchRequest, JobMatchResponse
from app.schemas.outreach import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    OutreachCopilotRequest,
    OutreachCopilotResponse,
    OutreachGenerateRequest,
    OutreachGenerateResponse,
)
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "ProfileCreate",
    "ProfileUpdate",
    "ProfileResponse",
    "JobCreate",
    "JobResponse",
    "AnswerGenerateRequest",
    "AnswerGenerateResponse",
    "ApplicationCreate",
    "ApplicationUpdate",
    "ApplicationResponse",
    "AuthRegisterRequest",
    "AuthLoginRequest",
    "AuthResponse",
    "JobMatchRequest",
    "JobMatchItem",
    "JobMatchResponse",
    "CoverLetterGenerateRequest",
    "CoverLetterGenerateResponse",
    "OutreachCopilotRequest",
    "OutreachCopilotResponse",
    "OutreachGenerateRequest",
    "OutreachGenerateResponse",
    "GeneratedContentCreate",
    "GeneratedContentResponse",
]
