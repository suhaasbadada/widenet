import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.authz import AuthenticatedUser, get_current_user, require_admin
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserSelfUpdate, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=dict)
def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Fetch the authenticated user's own record."""
    user = user_service.get_user(db=db, user_id=current_user.user_id)
    return {"success": True, "data": UserResponse.model_validate(user).model_dump()}


@router.put("/me", response_model=dict)
def update_me(
    payload: UserSelfUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Allow a user to update their own mutable profile fields."""
    try:
        user = user_service.update_user(
            db=db,
            user_id=current_user.user_id,
            payload=UserUpdate(name=payload.name, email=payload.email),
        )
    except user_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except user_service.UserConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"success": True, "data": UserResponse.model_validate(user).model_dump()}


@router.get("", response_model=dict)
def list_users(
    _: AuthenticatedUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """List all users for administrative workflows."""
    users = user_service.list_users(db=db)
    data = [UserResponse.model_validate(user).model_dump() for user in users]
    return {"success": True, "data": data}


@router.get("/{user_id}", response_model=dict)
def get_user(
    user_id: uuid.UUID,
    _: AuthenticatedUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Fetch a single user by id for administrative workflows."""
    try:
        user = user_service.get_user(db=db, user_id=user_id)
    except user_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"success": True, "data": UserResponse.model_validate(user).model_dump()}


@router.post("", response_model=dict, status_code=201)
def create_user(
    payload: UserCreate,
    _: AuthenticatedUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Create a user for administrative provisioning flows."""
    try:
        user = user_service.create_user(db=db, payload=payload)
    except user_service.UserConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"success": True, "data": UserResponse.model_validate(user).model_dump()}


@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    _: AuthenticatedUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Update an existing user's mutable attributes."""
    try:
        user = user_service.update_user(db=db, user_id=user_id, payload=payload)
    except user_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except user_service.UserConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"success": True, "data": UserResponse.model_validate(user).model_dump()}


@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: uuid.UUID,
    _: AuthenticatedUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a user and rely on database cascades for dependent records."""
    try:
        user_service.delete_user(db=db, user_id=user_id)
    except user_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"success": True, "data": {"deleted": True, "user_id": str(user_id)}}