import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# Supabase uses a connection pooler (PgBouncer) in transaction mode,
# which is incompatible with prepared statements. Disabling them here
# prevents "prepared statement does not exist" errors under pooled connections.
engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-c statement_timeout=30000"},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and guarantees cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
