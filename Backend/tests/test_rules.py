from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)
Base.metadata.create_all(test_engine)


def override_get_db() -> Generator[Session, None, None]:
    with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_policy_rule_crud_and_validation() -> None:
    payload = {
        "name": "Safety glasses required",
        "observation_type": "missing_safety_glasses",
        "severity": "high",
        "is_enabled": True,
        "cooldown_seconds": 30,
    }

    create_response = client.post("/api/v1/rules", json=payload)
    assert create_response.status_code == 201

    created = create_response.json()
    rule_id = created["id"]
    assert created["name"] == "Safety glasses required"
    assert created["observation_type"] == "missing_safety_glasses"

    list_response = client.get("/api/v1/rules")
    assert list_response.status_code == 200
    assert list_response.json() == [created]

    detail_response = client.get(f"/api/v1/rules/{rule_id}")
    assert detail_response.status_code == 200
    assert detail_response.json() == created

    patch_response = client.patch(
        f"/api/v1/rules/{rule_id}",
        json={
            "severity": "critical",
            "cooldown_seconds": 60,
        },
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["severity"] == "critical"
    assert patch_response.json()["cooldown_seconds"] == 60

    duplicate_response = client.post("/api/v1/rules", json=payload)
    assert duplicate_response.status_code == 409

    invalid_response = client.post(
        "/api/v1/rules",
        json={
            **payload,
            "name": "Invalid cooldown rule",
            "cooldown_seconds": -1,
        },
    )
    assert invalid_response.status_code == 422

    missing_response = client.get("/api/v1/rules/999")
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Policy rule not found"}
