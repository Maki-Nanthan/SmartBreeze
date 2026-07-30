from fastapi import APIRouter, HTTPException, status

from app.services.persistence_service import PersistenceService

router = APIRouter(tags=["persistence"])
persistence_service = PersistenceService()


@router.get("/status", status_code=status.HTTP_200_OK)
def get_status() -> dict[str, object]:
    state = persistence_service.get_latest_state()
    if state is None:
        raise HTTPException(status_code=404, detail="No classroom state available")
    return {
        "student_count": state.student_count,
        "occupancy_level": state.occupancy_level.value,
        "ac_status": state.ac_status,
        "temperature": state.temperature,
        "control_mode": state.control_mode.value,
        "timestamp": state.timestamp.isoformat(),
    }


@router.get("/occupancy-history", status_code=status.HTTP_200_OK)
def get_occupancy_history() -> list[dict[str, object]]:
    return persistence_service.get_occupancy_history()


@router.get("/ac-events", status_code=status.HTTP_200_OK)
def get_ac_events() -> list[dict[str, object]]:
    return persistence_service.get_ac_events()


@router.get("/ac-running-time", status_code=status.HTTP_200_OK)
def get_ac_running_time() -> dict[str, float]:
    return {"total_minutes": persistence_service.get_ac_running_time()}
