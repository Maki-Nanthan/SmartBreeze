from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.database.database import get_engine, get_session_factory, init_db
from app.models.persistence import ACEventModel, ClassroomStateModel, OccupancyHistoryModel
from app.schemas.classroom_state import ClassroomState, ControlMode, OccupancyLevel


class PersistenceService:
    def __init__(self, db_url: str | None = None) -> None:
        self.db_url = db_url
        self.session_factory = get_session_factory(db_url)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        init_db(self.db_url)
        get_engine(self.db_url).connect().close()

    def save_state(self, state: ClassroomState) -> None:
        self._ensure_schema()
        with self.session_factory() as session:
            session.query(ClassroomStateModel).delete()
            session.add(
                ClassroomStateModel(
                    student_count=state.student_count,
                    occupancy_level=state.occupancy_level.value,
                    ac_status=state.ac_status,
                    temperature=state.temperature,
                    control_mode=state.control_mode.value,
                    timestamp=_to_datetime(state.timestamp),
                )
            )
            session.commit()

    def save_occupancy_history(self, state: ClassroomState) -> None:
        with self.session_factory() as session:
            session.add(
                OccupancyHistoryModel(
                    student_count=state.student_count,
                    occupancy_level=state.occupancy_level.value,
                    control_mode=state.control_mode.value,
                    timestamp=_to_datetime(state.timestamp),
                )
            )
            session.commit()

    def save_ac_event(self, state: ClassroomState, reason: str) -> None:
        with self.session_factory() as session:
            session.add(
                ACEventModel(
                    ac_status=state.ac_status,
                    temperature=state.temperature,
                    reason=reason,
                    timestamp=_to_datetime(state.timestamp),
                )
            )
            session.commit()

    def get_latest_state(self) -> ClassroomState | None:
        with self.session_factory() as session:
            record = session.query(ClassroomStateModel).order_by(ClassroomStateModel.id.desc()).first()
            if not record:
                return None
            return ClassroomState(
                student_count=record.student_count,
                occupancy_level=OccupancyLevel(record.occupancy_level),
                ac_status=record.ac_status,
                temperature=record.temperature,
                control_mode=ControlMode(record.control_mode),
                timestamp=_to_utc(record.timestamp),
            )

    def get_occupancy_history(self) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            rows = session.query(OccupancyHistoryModel).order_by(OccupancyHistoryModel.timestamp.asc()).all()
            return [
                {
                    "id": row.id,
                    "student_count": row.student_count,
                    "occupancy_level": row.occupancy_level,
                    "control_mode": row.control_mode,
                    "timestamp": _to_utc(row.timestamp).isoformat(),
                }
                for row in rows
            ]

    def get_ac_events(self) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            rows = session.query(ACEventModel).order_by(ACEventModel.timestamp.asc()).all()
            return [
                {
                    "id": row.id,
                    "ac_status": row.ac_status,
                    "temperature": row.temperature,
                    "reason": row.reason,
                    "timestamp": _to_utc(row.timestamp).isoformat(),
                }
                for row in rows
            ]

    def get_ac_running_time(self) -> float:
        with self.session_factory() as session:
            rows = session.query(ACEventModel).order_by(ACEventModel.timestamp.asc()).all()
            total_seconds = 0.0
            ac_start_time: datetime | None = None
            for row in rows:
                current_time = _to_utc(row.timestamp)
                if row.ac_status:
                    if ac_start_time is None:
                        ac_start_time = current_time
                else:
                    if ac_start_time is not None:
                        total_seconds += (current_time - ac_start_time).total_seconds()
                        ac_start_time = None
            return round(total_seconds / 60.0, 2)


def _to_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
