from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.observation import Observation
from app.models.policy_rule import PolicyRule


def evaluate_observation(session: Session, observation: Observation) -> list[Event]:
    """Create at most one event per matching rule inside its cooldown window."""
    rules = session.scalars(
        select(PolicyRule).where(
            PolicyRule.is_enabled.is_(True),
            PolicyRule.observation_type == observation.label,
        )
    )
    created: list[Event] = []
    for rule in rules:
        if observation.confidence < rule.confidence_threshold:
            continue
        if observation.duration_seconds < rule.min_duration_seconds:
            continue
        cutoff = observation.observed_at - timedelta(seconds=rule.cooldown_seconds)
        duplicate = session.scalar(
            select(Event.id)
            .where(
                Event.rule_id == rule.id,
                Event.camera_id == observation.camera_id,
                Event.track_id == observation.track_id,
                Event.occurred_at >= cutoff,
            )
            .limit(1)
        )
        if duplicate is not None:
            continue
        event = Event(
            observation_id=observation.id,
            rule_id=rule.id,
            camera_id=observation.camera_id,
            track_id=observation.track_id,
            violation_type=rule.observation_type,
            severity=rule.severity,
            occurred_at=observation.observed_at,
            evidence_path=observation.evidence_path,
            message=f"{rule.name} detected for track {observation.track_id}",
            rule_snapshot={
                "name": rule.name,
                "observation_type": rule.observation_type,
                "severity": rule.severity,
                "confidence_threshold": rule.confidence_threshold,
                "min_duration_seconds": rule.min_duration_seconds,
                "cooldown_seconds": rule.cooldown_seconds,
            },
        )
        session.add(event)
        created.append(event)
    return created
