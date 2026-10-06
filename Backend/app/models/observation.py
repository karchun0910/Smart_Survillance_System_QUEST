from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(100), index=True)
    track_id: Mapped[str] = mapped_column(String(100), index=True)
    label: Mapped[str] = mapped_column(String(100), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    bbox: Mapped[list[float]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(100))
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    recognized_identity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
