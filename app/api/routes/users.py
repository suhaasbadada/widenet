import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=dict)
def list_users(db: Session = Depends(get_db)) -> dict:
    """List all users for admin/testing workflows."""
    users = user_service.list_users(db=db)
    data = [UserResponse.model_validate(user).model_dump() for user in users]
    return {"success": True, "data": data}


@router.get("/{user_id}", response_model=dict)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Fetch a single user by id."""
    try:
        user = user_service.get_user(db=db, user_id=user_id)
    except user_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": UserResponse.model_validate(user).model_dump()}


@router.post("", response_model=dict, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> dict:
    """Create a user for downstream profile and application flows."""
    try:
        user = user_service.create_user(db=db, payload=payload)
    except user_service.UserConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {"success": True, "data": UserResponse.model_validate(user).model_dump()}


@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Update an existing user's email address."""
    try:
        user = user_service.update_user(db=db, user_id=user_id, payload=payload)
    except user_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except user_service.UserConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {"success": True, "data": UserResponse.model_validate(user).model_dump()}


@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Delete a user and rely on database cascades for dependent records."""
    try:
        user_service.delete_user(db=db, user_id=user_id)
    except user_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": {"deleted": True, "user_id": str(user_id)}}