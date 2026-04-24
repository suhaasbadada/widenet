import uuid
import os

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


class UserNotFoundError(LookupError):
    """Raised when a requested user does not exist."""


class UserConflictError(ValueError):
    """Raised when a user operation would violate a uniqueness constraint."""


def _normalize_email(email: str) -> str:
    return str(email).strip().lower()


def _normalize_name(name: str) -> str:
    normalized = str(name).strip()
    if not normalized:
        raise ValueError("User name cannot be empty.")
    return normalized


def get_bootstrap_admin_emails() -> set[str]:
    raw_admin_emails = os.environ.get("ADMIN_EMAILS", "")
    return {
        email.strip().lower()
        for email in raw_admin_emails.split(",")
        if email.strip()
    }


def get_default_role_for_email(email: str) -> UserRole:
    normalized_email = _normalize_email(email)
    if normalized_email in get_bootstrap_admin_emails():
        return UserRole.ADMIN
    return UserRole.USER


def list_users(db: Session) -> list[User]:
    """Return all users ordered by creation time, newest first."""
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def get_user(db: Session, user_id: uuid.UUID) -> User:
    """Fetch a single user by id."""
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User '{user_id}' does not exist.")
    return user


def create_user(db: Session, payload: UserCreate) -> User:
    """Create a new user after enforcing unique email addresses."""
    normalized_email = _normalize_email(str(payload.email))
    existing_user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if existing_user is not None:
        raise UserConflictError(f"User with email '{normalized_email}' already exists.")

    user = User(
        name=_normalize_name(payload.name),
        email=normalized_email,
        role=payload.role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: uuid.UUID, payload: UserUpdate) -> User:
    """Update an existing user's mutable attributes."""
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User '{user_id}' does not exist.")

    if payload.name is not None:
        user.name = _normalize_name(payload.name)

    if payload.email is not None:
        normalized_email = _normalize_email(str(payload.email))
        conflicting_user = db.scalar(
            select(User).where(func.lower(User.email) == normalized_email, User.id != user_id)
        )
        if conflicting_user is not None:
            raise UserConflictError(f"User with email '{normalized_email}' already exists.")
        user.email = normalized_email

    if payload.role is not None:
        user.role = payload.role.value

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: uuid.UUID) -> None:
    """Delete a user by id.

    Related profiles/applications/generated content are deleted by DB cascades.
    """
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User '{user_id}' does not exist.")

    db.delete(user)
    db.commit()


def sync_configured_admin_roles(db: Session) -> int:
    """Promote configured bootstrap admin emails to the admin role."""
    admin_emails = get_bootstrap_admin_emails()
    if not admin_emails:
        return 0

    users = list(
        db.scalars(
            select(User).where(
                func.lower(User.email).in_(admin_emails),
                User.role != UserRole.ADMIN.value,
            )
        ).all()
    )
    if not users:
        return 0

    for user in users:
        user.role = UserRole.ADMIN.value

    db.commit()
    return len(users)