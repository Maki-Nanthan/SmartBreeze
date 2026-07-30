from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

from app.database.database import init_db
from app.schemas.classroom_state import ClassroomState, ControlMode, OccupancyLevel
from app.services.persistence_service import PersistenceService


def test_persistence_round_trip(tmp_path: str) -> None:
    db_path = str(tmp_path / "test.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    init_db(f"sqlite:///{db_path}")

    service = PersistenceService(f"sqlite:///{db_path}")
    state = ClassroomState(
        student_count=10,
        occupancy_level=OccupancyLevel.HIGH,
        ac_status=True,
        temperature=20.0,
        control_mode=ControlMode.AI_SIMULATION,
        timestamp=datetime.now(timezone.utc),
    )

    service.save_state(state)
    service.save_occupancy_history(state)
    service.save_ac_event(state, reason="student_arriving")

    stored_state = service.get_latest_state()
    history = service.get_occupancy_history()
    events = service.get_ac_events()
    running_time = service.get_ac_running_time()

    assert stored_state is not None
    assert stored_state.student_count == 10
    assert stored_state.occupancy_level == OccupancyLevel.HIGH
    assert len(history) == 1
    assert history[0]["student_count"] == 10
    assert len(events) == 1
    assert events[0]["reason"] == "student_arriving"
    assert running_time == 0.0
