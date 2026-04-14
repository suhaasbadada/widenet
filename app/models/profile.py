import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Public URL pointing to the uploaded file in Supabase Storage
    resume_url: Mapped[str | None] = mapped_column(String, nullable=True)
    # Raw text extracted from the resume file; used for all AI processing
    raw_resume: Mapped[str | None] = mapped_column(Text, nullable=True)
    # AI-parsed resume fields stored as structured JSONB
    structured_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    headline: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
