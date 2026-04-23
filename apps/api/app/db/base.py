from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models.

    Import this in every model file and it will be picked up automatically
    by Alembic or any metadata-based migration tooling.
    """
    pass
