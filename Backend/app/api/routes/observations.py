from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.observation import Observation
from app.schemas.event import EventRead
from app.schemas.observation import ObservationCreate, ObservationRead
from app.services.policy_engine import evaluate_observation

router = APIRouter(prefix="/observations")
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_observation(payload: ObservationCreate, session: DatabaseSession) -> dict[str, object]:
    observation = Observation(**payload.model_dump())
    session.add(observation)
    session.flush()
    events = evaluate_observation(session, observation)
    session.commit()
    session.refresh(observation)
    for event in events:
        session.refresh(event)
    return {
        "observation": ObservationRead.model_validate(observation),
        "events": [EventRead.model_validate(event) for event in events],
    }


@router.get("", response_model=list[ObservationRead])
def list_observations(
    session: DatabaseSession,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[Observation]:
    return list(
        session.scalars(select(Observation).order_by(Observation.observed_at.desc()).limit(limit))
    )
