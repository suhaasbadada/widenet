import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.profile import ProfileResponse
from app.services import profile_service

router = APIRouter(tags=["profiles"])


@router.get("/profiles/{user_id}", response_model=dict)
def get_profile(user_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Fetch the latest stored profile for a user."""
    try:
        profile = profile_service.get_profile_by_user(db=db, user_id=user_id)
    except profile_service.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": ProfileResponse.model_validate(profile).model_dump()}


@router.put("/profiles/{user_id}/refresh", response_model=dict)
@router.put("/profile/{user_id}/refresh", response_model=dict, include_in_schema=False)
def refresh_profile(user_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Reprocess a user's stored resume and update their structured profile."""
    try:
        profile = profile_service.refresh_profile(db=db, user_id=user_id)
    except profile_service.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (profile_service.ProfileRefreshError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"success": True, "data": ProfileResponse.model_validate(profile).model_dump()}
