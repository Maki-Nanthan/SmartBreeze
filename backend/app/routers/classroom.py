from fastapi import APIRouter, HTTPException, status

from app.schemas.classroom_state import ClassroomState
from app.schemas.manual_control_request import ManualControlRequest
from app.schemas.occupancy_request import OccupancyRequest
from app.services.ac_control_service import ACControlService
from app.services.classroom_service import ClassroomService
from app.services.manual_control_service import ManualControlService
from app.services.persistence_service import PersistenceService

router = APIRouter(tags=["classroom"])
persistence_service = PersistenceService()
latest_state = persistence_service.get_latest_state()

service = ClassroomService(initial_state=latest_state)
ac_service = ACControlService()
manual_service = ManualControlService()


@router.get("/classroom/state", response_model=ClassroomState)
def get_classroom_state() -> ClassroomState:
    return service.get_state()


@router.post("/classroom/state", response_model=ClassroomState, status_code=status.HTTP_200_OK)
def update_classroom_state(payload: ClassroomState) -> ClassroomState:
    try:
        state = service.update_state(**payload.model_dump())
        persistence_service.save_state(state)
        persistence_service.save_occupancy_history(state)
        persistence_service.save_ac_event(state, reason="classroom_state_update")
        return state
    except Exception as exc:  # pragma: no cover - basic fallback
        raise HTTPException(status_code=500, detail="Unable to update classroom state") from exc


@router.post("/occupancy", response_model=ClassroomState, status_code=status.HTTP_200_OK)
def update_occupancy(payload: OccupancyRequest) -> ClassroomState:
    try:
        state = ac_service.apply_request(payload)
        service.update_state(**state.model_dump())
        persistence_service.save_state(state)
        persistence_service.save_occupancy_history(state)
        persistence_service.save_ac_event(state, reason="occupancy_update")
        return state
    except Exception as exc:  # pragma: no cover - basic fallback
        raise HTTPException(status_code=500, detail="Unable to process occupancy request") from exc


@router.post("/manual-control", response_model=ClassroomState, status_code=status.HTTP_200_OK)
def apply_manual_control(payload: ManualControlRequest) -> ClassroomState:
    try:
        state = manual_service.apply_manual_control(payload)
        service.update_state(**state.model_dump())
        return state
    except Exception as exc:  # pragma: no cover - basic fallback
        raise HTTPException(status_code=500, detail="Unable to apply manual control") from exc
