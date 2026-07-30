from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path):
    db_path = tmp_path / "manual.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    import app.core.config as config_module
    import app.database.database as database_module
    import app.database.base as base_module
    import app.main as main_module
    import app.services.persistence_service as persistence_service_module

    config_module.settings = config_module.Settings()
    base_module.Base.metadata.drop_all(bind=database_module.get_engine())
    importlib.reload(database_module)
    importlib.reload(main_module)
    importlib.reload(persistence_service_module)

    database_module.init_db()

    with TestClient(main_module.app) as test_client:
        yield test_client


def test_manual_control_updates_state_and_persistence(client: TestClient) -> None:
    response = client.post(
        "/api/manual-control",
        json={
            "student_count": 12,
            "ac_status": True,
            "temperature": 22.0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["student_count"] == 12
    assert payload["occupancy_level"] == "HIGH"
    assert payload["ac_status"] is True
    assert payload["temperature"] == 22.0
    assert payload["control_mode"] == "MANUAL"

    status_response = client.get("/api/status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["student_count"] == 12
    assert status_payload["occupancy_level"] == "HIGH"
    assert status_payload["control_mode"] == "MANUAL"

    import app.services.persistence_service as persistence_service_module

    persistence_service = persistence_service_module.PersistenceService()
    history = persistence_service.get_occupancy_history()
    events = persistence_service.get_ac_events()
    assert len(history) == 1
    assert history[0]["student_count"] == 12
    assert history[0]["occupancy_level"] == "HIGH"
    assert len(events) == 1
    assert events[0]["reason"] == "manual_control"


def test_manual_control_thresholds(client: TestClient) -> None:
    res = client.post("/api/manual-control", json={"student_count": 0})
    assert res.status_code == 200
    assert res.json()["occupancy_level"] == "LOW"

    res = client.post("/api/manual-control", json={"student_count": 5})
    assert res.status_code == 200
    assert res.json()["occupancy_level"] == "MEDIUM"

    res = client.post("/api/manual-control", json={"student_count": 12})
    assert res.status_code == 200
    assert res.json()["occupancy_level"] == "HIGH"
