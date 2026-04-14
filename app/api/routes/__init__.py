from fastapi import APIRouter

from app.api.routes import auth, upload, users

# Single aggregation point: add new route modules here as the project grows.
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(upload.router)
api_router.include_router(users.router)
