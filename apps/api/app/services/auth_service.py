from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, ensure_jwt_configured, hash_password, verify_password
from app.models.auth_credential import AuthCredential
from app.models.user import User
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, ChangePasswordRequest
from app.services import user_service


class AuthConflictError(ValueError):
    """Raised when a registration request conflicts with an existing account."""


class InvalidCredentialsError(ValueError):
    """Raised when login credentials are invalid."""


class InvalidCurrentPasswordError(ValueError):
    """Raised when the supplied current password does not match the stored credential."""


class CredentialNotFoundError(ValueError):
    """Raised when a password credential does not exist for the target user."""


def register_user(db: Session, payload: AuthRegisterRequest) -> tuple[User, str]:
    """Create a user account with password-based credentials and return a JWT."""
    ensure_jwt_configured()
    normalized_email = user_service._normalize_email(str(payload.email))
    default_role = user_service.get_default_role_for_email(normalized_email)
    normalized_name = user_service._normalize_name(payload.name)

    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if user is None:
        user = User(name=normalized_name, email=normalized_email, role=default_role.value)
        db.add(user)
        db.flush()
    elif not getattr(user, "role", None):
        user.role = default_role.value

    if normalized_name and not getattr(user, "name", None):
        user.name = normalized_name

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

    access_token = create_access_token(user_id=str(user.id), email=user.email, role=user.role)
    return user, access_token


def login_user(db: Session, payload: AuthLoginRequest) -> tuple[User, str]:
    """Authenticate a user by email and password and return a JWT."""
    ensure_jwt_configured()
    normalized_email = user_service._normalize_email(str(payload.email))

    user = db.scalar(select(User).where(func.lower(User.email) == normalized_email))
    if user is None:
        raise InvalidCredentialsError("Invalid email or password.")

    credential = db.get(AuthCredential, user.id)
    if credential is None or not verify_password(payload.password, credential.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    if not getattr(user, "role", None):
        user.role = user_service.get_default_role_for_email(user.email).value
        db.commit()
        db.refresh(user)

    access_token = create_access_token(user_id=str(user.id), email=user.email, role=user.role)
    return user, access_token


def change_password(db: Session, user_id: str, payload: ChangePasswordRequest) -> None:
    """Rotate a user's password after verifying the current password."""
    credential = db.get(AuthCredential, user_id)
    if credential is None:
        raise CredentialNotFoundError("Password credential does not exist for this account.")

    if not verify_password(payload.current_password, credential.password_hash):
        raise InvalidCurrentPasswordError("Current password is incorrect.")

    credential.password_hash = hash_password(payload.new_password)
    db.add(credential)
    db.commit()