from __future__ import annotations

import pytest

from app.schemas.classroom_state import ControlMode, OccupancyLevel
from app.services.ac_control_service import ACControlService


@pytest.mark.parametrize(
    ("student_count", "expected_level", "expected_ac", "expected_temp"),
    [
        (1, OccupancyLevel.LOW, False, None),
        (2, OccupancyLevel.LOW, False, None),
        (3, OccupancyLevel.MEDIUM, True, 24.0),
        (9, OccupancyLevel.MEDIUM, True, 24.0),
        (10, OccupancyLevel.HIGH, True, 20.0),
        (35, OccupancyLevel.HIGH, True, 20.0),
    ],
)
def test_ac_control_rules(student_count: int, expected_level: OccupancyLevel, expected_ac: bool, expected_temp: float | None) -> None:
    service = ACControlService()
    state = service.resolve_state(student_count=student_count)

    assert state.student_count == student_count
    assert state.occupancy_level == expected_level
    assert state.ac_status is expected_ac
    assert state.temperature == expected_temp
    assert state.control_mode == ControlMode.EDGE_AI


@pytest.mark.parametrize(
    ("occupancy_level", "expected_ac", "expected_temp"),
    [
        (OccupancyLevel.LOW, False, None),
        (OccupancyLevel.MEDIUM, True, 24.0),
        (OccupancyLevel.HIGH, True, 20.0),
    ],
)
def test_ac_control_rules_from_occupancy_level(occupancy_level: OccupancyLevel, expected_ac: bool, expected_temp: float | None) -> None:
    service = ACControlService()
    state = service.resolve_state(occupancy_level=occupancy_level)

    assert state.occupancy_level == occupancy_level
    assert state.ac_status is expected_ac
    assert state.temperature == expected_temp
    assert state.control_mode == ControlMode.EDGE_AI
