import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import UserRole

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


def initialize_database() -> None:
    """Create missing tables and apply lightweight schema fixes required by the app."""
    import app.models  # noqa: F401 - register SQLAlchemy models before create_all

    Base.metadata.create_all(bind=engine)
    _ensure_user_role_column()
    _sync_bootstrap_admin_roles()


def _ensure_user_role_column() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "role" not in column_names:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"
                )
            )
        else:
            connection.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user'"))
            connection.execute(text("ALTER TABLE users ALTER COLUMN role SET NOT NULL"))


def _sync_bootstrap_admin_roles() -> None:
    from app.services import user_service

    db = SessionLocal()
    try:
        user_service.sync_configured_admin_roles(db)
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and guarantees cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
