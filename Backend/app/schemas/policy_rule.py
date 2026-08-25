from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["low", "medium", "high", "critical"]


class PolicyRuleCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str = Field(min_length=1, max_length=100)
    observation_type: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    severity: Severity = "medium"
    is_enabled: bool = True
    cooldown_seconds: int = Field(default=30, ge=0)


class PolicyRuleUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str | None = Field(default=None, min_length=1, max_length=100)
    observation_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    severity: Severity | None = None
    is_enabled: bool | None = None
    cooldown_seconds: int | None = Field(default=None, ge=0)


class PolicyRuleRead(PolicyRuleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
