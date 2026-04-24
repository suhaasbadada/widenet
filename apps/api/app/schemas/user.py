import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.user import UserRole


NonEmptyName = Annotated[str, Field(min_length=1, max_length=255)]


class UserCreate(BaseModel):
    name: NonEmptyName
    email: EmailStr
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    name: NonEmptyName | None = None
    email: EmailStr | None = None
    role: UserRole | None = None

    @model_validator(mode="after")
    def validate_non_empty_update(self) -> "UserUpdate":
        if self.name is None and self.email is None and self.role is None:
            raise ValueError("At least one of 'name', 'email', or 'role' must be provided.")
        return self


class UserSelfUpdate(BaseModel):
    name: NonEmptyName | None = None
    email: EmailStr | None = None

    @model_validator(mode="after")
    def validate_non_empty_update(self) -> "UserSelfUpdate":
        if self.name is None and self.email is None:
            raise ValueError("At least one of 'name' or 'email' must be provided.")
        return self


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}
