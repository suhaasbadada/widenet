from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.db.session import initialize_database

app = FastAPI(title="Widenet API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All versioned routes are aggregated in app/api/routes/__init__.py.
# New route modules only need to be registered there, not here.
app.include_router(api_router)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}