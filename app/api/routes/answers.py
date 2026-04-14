from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.answer import AnswerGenerateRequest
from app.services import answer_service

router = APIRouter(prefix="/answers", tags=["answers"])


@router.post("/generate", response_model=dict)
def generate_answer(payload: AnswerGenerateRequest, db: Session = Depends(get_db)) -> dict:
    """Generate a concise, job-specific application answer."""
    try:
        response = answer_service.generate_answer(db=db, payload=payload)
    except answer_service.ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except answer_service.JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return response.model_dump()
