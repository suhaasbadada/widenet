from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.authz import AuthenticatedUser, get_current_user
from app.core.security import InvalidTokenError, SecurityConfigurationError, decode_access_token
from app.db.session import get_db
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, AuthResponse, ChangePasswordRequest
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/register", response_model=dict, status_code=201)
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)) -> dict:
    """Register a password-based account and immediately issue an access token."""
    try:
        user, access_token = auth_service.register_user(db=db, payload=payload)
    except auth_service.AuthConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except SecurityConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    response = AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )
    return {"success": True, "data": response.model_dump()}


@router.post("/login", response_model=dict)
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> dict:
    """Authenticate an existing account and issue an access token."""
    try:
        user, access_token = auth_service.login_user(db=db, payload=payload)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except SecurityConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    response = AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )
    return {"success": True, "data": response.model_dump()}


@router.post("/logout", response_model=dict)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> dict:
    """Validate the current token and instruct the client to discard it.

    JWT logout is stateless for this MVP, so the server does not persist a
    denylist. The caller should delete the token client-side after success.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication credentials were not provided.")

    try:
        decode_access_token(credentials.credentials)
    except (InvalidTokenError, SecurityConfigurationError) as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    return {"success": True, "data": {"logged_out": True}}


@router.post("/change-password", response_model=dict)
def change_password(
    payload: ChangePasswordRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Change the authenticated user's password after validating current credentials."""
    try:
        auth_service.change_password(db=db, user_id=str(current_user.user_id), payload=payload)
    except (auth_service.InvalidCurrentPasswordError, auth_service.CredentialNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"success": True, "data": {"password_changed": True}}