from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, ensure_jwt_configured, hash_password, verify_password
from app.models.auth_credential import AuthCredential
from app.models.user import User
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest


class AuthConflictError(ValueError):
    """Raised when a registration request conflicts with an existing account."""


class InvalidCredentialsError(ValueError):
    """Raised when login credentials are invalid."""


def register_user(db: Session, payload: AuthRegisterRequest) -> tuple[User, str]:
    """Create a user account with password-based credentials and return a JWT."""
    ensure_jwt_configured()
    normalized_email = str(payload.email).strip().lower()

    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if user is None:
        user = User(email=normalized_email)
        db.add(user)
        db.flush()

    credential = db.get(AuthCredential, user.id)
    if credential is not None:
        raise AuthConflictError(f"User with email '{normalized_email}' is already registered.")

    credential = AuthCredential(
        user_id=user.id,
        password_hash=hash_password(payload.password),
    )
    db.add(credential)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user_id=str(user.id), email=user.email)
    return user, access_token


def login_user(db: Session, payload: AuthLoginRequest) -> tuple[User, str]:
    """Authenticate a user by email and password and return a JWT."""
    ensure_jwt_configured()
    normalized_email = str(payload.email).strip().lower()

    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if user is None:
        raise InvalidCredentialsError("Invalid email or password.")

    credential = db.get(AuthCredential, user.id)
    if credential is None or not verify_password(payload.password, credential.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    access_token = create_access_token(user_id=str(user.id), email=user.email)
    return user, access_token