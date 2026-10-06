from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import Event
from app.schemas.event import EventRead, EventReviewUpdate

router = APIRouter(prefix="/events")
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[EventRead])
def list_events(
    session: DatabaseSession,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[Event]:
    return list(session.scalars(select(Event).order_by(Event.occurred_at.desc()).limit(limit)))


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: int, session: DatabaseSession) -> Event:
    event = session.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.patch("/{event_id}/review", response_model=EventRead)
def review_event(
    event_id: int,
    payload: EventReviewUpdate,
    session: DatabaseSession,
) -> Event:
    event = session.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    event.review_status = payload.review_status
    session.commit()
    session.refresh(event)
    return event
