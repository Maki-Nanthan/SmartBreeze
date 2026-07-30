from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.classroom_state import ClassroomState, ControlMode, OccupancyLevel
from app.schemas.occupancy_request import OccupancyRequest


@dataclass(frozen=True)
class OccupancyThresholds:
    medium_threshold: int = settings.medium_threshold
    high_threshold: int = settings.high_threshold


class ACControlService:
    def __init__(self, thresholds: OccupancyThresholds | None = None) -> None:
        self.thresholds = thresholds or OccupancyThresholds()

    def resolve_state(self, *, student_count: int | None = None, occupancy_level: OccupancyLevel | None = None) -> ClassroomState:
        if occupancy_level is not None:
            derived_level = occupancy_level
            if student_count is None:
                if derived_level == OccupancyLevel.HIGH:
                    student_count = self.thresholds.high_threshold
                elif derived_level == OccupancyLevel.MEDIUM:
                    student_count = self.thresholds.medium_threshold
                else:
                    student_count = 0
        elif student_count is not None:
            derived_level = self._derive_occupancy_level(student_count)
        else:
            derived_level = OccupancyLevel.LOW
            student_count = 0

        return ClassroomState(
            student_count=student_count,
            occupancy_level=derived_level,
            ac_status=self._ac_status_for_level(derived_level),
            temperature=self._temperature_for_level(derived_level),
            control_mode=ControlMode.EDGE_AI,
            timestamp=datetime.now(timezone.utc),
        )

    def apply_request(self, payload: OccupancyRequest) -> ClassroomState:
        return self.resolve_state(
            student_count=payload.student_count,
            occupancy_level=payload.occupancy_level,
        )

    def _derive_occupancy_level(self, student_count: int) -> OccupancyLevel:
        if student_count >= self.thresholds.high_threshold:
            return OccupancyLevel.HIGH
        if student_count >= self.thresholds.medium_threshold:
            return OccupancyLevel.MEDIUM
        return OccupancyLevel.LOW

    def _ac_status_for_level(self, occupancy_level: OccupancyLevel) -> bool:
        return occupancy_level in {OccupancyLevel.MEDIUM, OccupancyLevel.HIGH}

    def _temperature_for_level(self, occupancy_level: OccupancyLevel) -> float | None:
        if occupancy_level == OccupancyLevel.MEDIUM:
            return 24.0
        if occupancy_level == OccupancyLevel.HIGH:
            return 20.0
        return None
