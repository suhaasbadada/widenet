import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserNotFoundError(LookupError):
    """Raised when a requested user does not exist."""


class UserConflictError(ValueError):
    """Raised when a user operation would violate a uniqueness constraint."""


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
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise UserConflictError(f"User with email '{payload.email}' already exists.")

    user = User(email=str(payload.email))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: uuid.UUID, payload: UserUpdate) -> User:
    """Update an existing user's email address."""
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User '{user_id}' does not exist.")

    conflicting_user = db.scalar(
        select(User).where(User.email == payload.email, User.id != user_id)
    )
    if conflicting_user is not None:
        raise UserConflictError(f"User with email '{payload.email}' already exists.")

    user.email = str(payload.email)
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