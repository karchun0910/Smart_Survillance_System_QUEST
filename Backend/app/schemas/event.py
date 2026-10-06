from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ReviewStatus = Literal["pending", "confirmed", "false_alarm"]


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    observation_id: int
    rule_id: int
    camera_id: str
    track_id: str
    violation_type: str
    severity: str
    occurred_at: datetime
    review_status: ReviewStatus
    evidence_path: str | None
    message: str
    rule_snapshot: dict[str, object]
    created_at: datetime


class EventReviewUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_status: ReviewStatus
