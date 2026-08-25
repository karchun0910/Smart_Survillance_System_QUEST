from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import cameras
from app.main import app

client = TestClient(app)


def test_camera_status(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(cameras, "check_camera", lambda source: True)

    response = client.get("/api/v1/cameras/status")

    assert response.status_code == 200
    assert response.json() == {
        "source": 0,
        "available": True,
    }
