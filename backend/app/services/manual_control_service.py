from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.classroom_state import ClassroomState, ControlMode, OccupancyLevel
from app.schemas.manual_control_request import ManualControlRequest
from app.services.persistence_service import PersistenceService
from app.services.ac_control_service import ACControlService


class ManualControlService:
    def __init__(self, persistence_service: PersistenceService | None = None, ac_service: ACControlService | None = None) -> None:
        self.persistence_service = persistence_service or PersistenceService()
        self.ac_service = ac_service or ACControlService()

    def apply_manual_control(self, payload: ManualControlRequest) -> ClassroomState:
        current_state = self.persistence_service.get_latest_state()
        if current_state is None:
            current_state = ClassroomState(
                student_count=0,
                occupancy_level=OccupancyLevel.LOW,
                ac_status=False,
                temperature=None,
                control_mode=ControlMode.EDGE_AI,
                timestamp=datetime.now(timezone.utc),
            )

        new_student_count = payload.student_count if payload.student_count is not None else current_state.student_count
        derived_level = self.ac_service._derive_occupancy_level(new_student_count)

        state = current_state.model_copy(update={
            "student_count": new_student_count,
            "occupancy_level": derived_level,
            "ac_status": payload.ac_status if payload.ac_status is not None else current_state.ac_status,
            "temperature": payload.temperature if payload.temperature is not None else current_state.temperature,
            "control_mode": ControlMode.MANUAL,
            "timestamp": datetime.now(timezone.utc),
        })

        self.persistence_service.save_state(state)
        self.persistence_service.save_occupancy_history(state)
        self.persistence_service.save_ac_event(state, reason="manual_control")
        return state
