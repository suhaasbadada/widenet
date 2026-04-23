import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, model_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: UserRole | None = None

    @model_validator(mode="after")
    def validate_non_empty_update(self) -> "UserUpdate":
        if self.email is None and self.role is None:
            raise ValueError("At least one of 'email' or 'role' must be provided.")
        return self


class UserSelfUpdate(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}
