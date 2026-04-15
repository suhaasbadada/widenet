from fastapi import APIRouter

from app.api.routes import answers, applications, auth, job_match, jobs, outreach, profiles, upload, users

# Single aggregation point: add new route modules here as the project grows.
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(answers.router)
api_router.include_router(applications.router)
api_router.include_router(auth.router)
api_router.include_router(job_match.router)
api_router.include_router(jobs.router)
api_router.include_router(outreach.router)
api_router.include_router(profiles.router)
api_router.include_router(upload.router)
api_router.include_router(users.router)
