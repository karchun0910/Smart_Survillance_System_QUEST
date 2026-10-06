from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ObservationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    camera_id: str = Field(min_length=1, max_length=100)
    track_id: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    confidence: float = Field(ge=0, le=1)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    bbox: list[float] = Field(min_length=4, max_length=4)
    model_version: str = Field(min_length=1, max_length=100)
    duration_seconds: float = Field(default=0, ge=0)
    recognized_identity: str | None = Field(default=None, max_length=100)
    evidence_path: str | None = None

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, value: list[float]) -> list[float]:
        if any(number < 0 for number in value):
            raise ValueError("bbox coordinates must be non-negative")
        if value[2] <= value[0] or value[3] <= value[1]:
            raise ValueError("bbox must be [x1, y1, x2, y2]")
        return value


class ObservationRead(ObservationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
