import pytest
from sqlalchemy import delete

from app.models.event import Event
from app.models.observation import Observation
from app.models.policy_rule import PolicyRule
from tests.test_rules import TestSessionLocal, client


@pytest.fixture(autouse=True)
def clean_observation_tables():
    with TestSessionLocal() as session:
        session.execute(delete(Event))
        session.execute(delete(Observation))
        session.execute(delete(PolicyRule))
        session.commit()
    yield
    with TestSessionLocal() as session:
        session.execute(delete(Event))
        session.execute(delete(Observation))
        session.execute(delete(PolicyRule))
        session.commit()


def _observation(
    confidence: float = 0.9,
    label: str = "knife_visible",
    duration_seconds: float = 2,
) -> dict[str, object]:
    return {
        "camera_id": "camera-test",
        "track_id": "track-1",
        "label": label,
        "confidence": confidence,
        "observed_at": "2026-09-08T10:00:00Z",
        "bbox": [10, 20, 80, 120],
        "model_version": "rfdetr-nano-test",
        "duration_seconds": duration_seconds,
    }


def test_observation_policy_cooldown_and_review() -> None:
    rule = client.post(
        "/api/v1/rules",
        json={
            "name": "Test knife alert",
            "observation_type": "knife_visible",
            "severity": "high",
            "cooldown_seconds": 30,
            "confidence_threshold": 0.8,
        },
    )
    assert rule.status_code == 201

    first = client.post("/api/v1/observations", json=_observation())
    assert first.status_code == 201
    assert len(first.json()["events"]) == 1

    duplicate = client.post("/api/v1/observations", json=_observation())
    assert duplicate.status_code == 201
    assert duplicate.json()["events"] == []

    low_confidence = client.post("/api/v1/observations", json=_observation(confidence=0.5))
    assert low_confidence.status_code == 201
    assert low_confidence.json()["events"] == []

    events = client.get("/api/v1/events")
    assert events.status_code == 200
    event_id = events.json()[0]["id"]
    review = client.patch(
        f"/api/v1/events/{event_id}/review",
        json={"review_status": "confirmed"},
    )
    assert review.status_code == 200
    assert review.json()["review_status"] == "confirmed"


def test_missing_lab_coat_requires_three_seconds() -> None:
    rule = client.post(
        "/api/v1/rules",
        json={
            "name": "Lab coat required",
            "observation_type": "missing_lab_coat",
            "severity": "high",
            "cooldown_seconds": 30,
            "confidence_threshold": 0.5,
            "min_duration_seconds": 3,
        },
    )
    assert rule.status_code == 201

    early = client.post(
        "/api/v1/observations",
        json=_observation(label="missing_lab_coat", duration_seconds=2.9),
    )
    assert early.status_code == 201
    assert early.json()["events"] == []

    confirmed = client.post(
        "/api/v1/observations",
        json=_observation(label="missing_lab_coat", duration_seconds=3),
    )
    assert confirmed.status_code == 201
    assert confirmed.json()["events"][0]["violation_type"] == "missing_lab_coat"


def test_missing_long_pants_applies_confidence_duration_and_cooldown() -> None:
    rule = client.post(
        "/api/v1/rules",
        json={
            "name": "Long pants required",
            "observation_type": "missing_long_pants",
            "severity": "medium",
            "cooldown_seconds": 30,
            "confidence_threshold": 0.8,
            "min_duration_seconds": 3,
        },
    )
    assert rule.status_code == 201

    low_confidence = client.post(
        "/api/v1/observations",
        json=_observation(
            confidence=0.79,
            label="missing_long_pants",
            duration_seconds=3,
        ),
    )
    assert low_confidence.status_code == 201
    assert low_confidence.json()["events"] == []

    too_early = client.post(
        "/api/v1/observations",
        json=_observation(label="missing_long_pants", duration_seconds=2.9),
    )
    assert too_early.status_code == 201
    assert too_early.json()["events"] == []

    confirmed = client.post(
        "/api/v1/observations",
        json=_observation(label="missing_long_pants", duration_seconds=3),
    )
    assert confirmed.status_code == 201
    assert confirmed.json()["events"][0]["violation_type"] == "missing_long_pants"

    duplicate = client.post(
        "/api/v1/observations",
        json=_observation(label="missing_long_pants", duration_seconds=4),
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["events"] == []
