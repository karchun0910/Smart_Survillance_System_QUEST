from datetime import UTC, datetime

import cv2
from pytest import MonkeyPatch
from sqlalchemy import delete

from app.models.observation import Observation
from tests.test_rules import TestSessionLocal, client


def test_camera_status_uses_recent_detector_observation() -> None:
    with TestSessionLocal() as session:
        session.execute(delete(Observation))
        session.add(
            Observation(
                camera_id="camera-0",
                track_id="1",
                label="person_present",
                confidence=0.9,
                observed_at=datetime.now(UTC),
                bbox=[10, 20, 80, 120],
                model_version="rfdetr-nano-test",
                duration_seconds=1,
            )
        )
        session.commit()

    response = client.get("/api/v1/cameras/status")

    assert response.status_code == 200
    assert response.json() == {
        "source": 0,
        "available": True,
    }


def test_camera_status_does_not_open_webcam(monkeypatch: MonkeyPatch) -> None:
    def fail_if_opened(source: int) -> None:
        raise AssertionError(f"Webcam {source} was opened by the status endpoint")

    monkeypatch.setattr(cv2, "VideoCapture", fail_if_opened)
    with TestSessionLocal() as session:
        session.execute(delete(Observation))
        session.commit()

    response = client.get("/api/v1/cameras/status")

    assert response.status_code == 200
    assert response.json() == {
        "source": 0,
        "available": False,
    }
