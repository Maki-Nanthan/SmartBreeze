from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.classroom_state import ClassroomState, ControlMode, OccupancyLevel


class ClassroomService:
    def __init__(self, initial_state: ClassroomState | None = None) -> None:
        if initial_state:
            self._state = initial_state
        else:
            self._state = ClassroomState(
                student_count=0,
                occupancy_level=OccupancyLevel.LOW,
                ac_status=False,
                temperature=None,
                control_mode=ControlMode.EDGE_AI,
                timestamp=datetime.now(timezone.utc),
            )

    def get_state(self) -> ClassroomState:
        return self._state

    def update_state(self, **kwargs: object) -> ClassroomState:
        data = self._state.model_dump(by_alias=True)
        data.update(kwargs)
        data["timestamp"] = datetime.now(timezone.utc)
        self._state = ClassroomState(**data)
        return self._state
