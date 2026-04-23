import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, SecurityConfigurationError, decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

_bearer_scheme = HTTPBearer(auto_error=True)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: uuid.UUID
    email: str
    role: UserRole


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    try:
        token_payload = decode_access_token(credentials.credentials)
        resolved_user_id = uuid.UUID(str(token_payload["sub"]))
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except SecurityConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    user = db.get(User, resolved_user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Authenticated user no longer exists.")

    return AuthenticatedUser(
        user_id=user.id,
        email=user.email,
        role=UserRole(user.role or UserRole.USER.value),
    )


def require_admin(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access is required for this endpoint.")
    return current_user