from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.observation import Observation

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/cameras/status")
def camera_status(session: DatabaseSession) -> dict[str, object]:
    source = int(get_settings().camera_source)
    recent_observation = session.scalar(
        select(Observation.id)
        .where(
            Observation.camera_id == f"camera-{source}",
            Observation.observed_at >= datetime.now(UTC) - timedelta(seconds=5),
        )
        .limit(1)
    )

    return {
        "source": source,
        "available": recent_observation is not None,
    }
