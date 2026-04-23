import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from app.services import application_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=dict, status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)) -> dict:
    """Create a new application record."""
    try:
        application = application_service.create_application(db=db, payload=payload)
    except application_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except application_service.JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except application_service.DuplicateApplicationError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {"success": True, "data": ApplicationResponse.model_validate(application).model_dump()}


@router.get("", response_model=dict)
def list_applications(
    user_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """List applications, with optional user-based filtering."""
    applications = application_service.get_applications(db=db, user_id=user_id)
    data = [ApplicationResponse.model_validate(item).model_dump() for item in applications]
    return {"success": True, "data": data}


@router.get("/{application_id}", response_model=dict)
def get_application(application_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    """Fetch a single application by id."""
    try:
        application = application_service.get_application_by_id(db=db, application_id=application_id)
    except application_service.ApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": ApplicationResponse.model_validate(application).model_dump()}


@router.put("/{application_id}", response_model=dict)
def update_application_status(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Update an application's status."""
    try:
        application = application_service.update_application_status(
            db=db,
            application_id=application_id,
            payload=payload,
        )
    except application_service.ApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"success": True, "data": ApplicationResponse.model_validate(application).model_dump()}
