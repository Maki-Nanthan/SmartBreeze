from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from app.database.base import Base


class ClassroomStateModel(Base):
    __tablename__ = "classroom_states"

    id = Column(Integer, primary_key=True, index=True)
    student_count = Column(Integer, nullable=False, default=0)
    occupancy_level = Column(String, nullable=False, default="LOW")
    ac_status = Column(Boolean, nullable=False, default=False)
    temperature = Column(Float, nullable=True)
    control_mode = Column(String, nullable=False, default="AI_SIMULATION")
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)


class OccupancyHistoryModel(Base):
    __tablename__ = "occupancy_history"

    id = Column(Integer, primary_key=True, index=True)
    student_count = Column(Integer, nullable=False)
    occupancy_level = Column(String, nullable=False)
    control_mode = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)


class ACEventModel(Base):
    __tablename__ = "ac_events"

    id = Column(Integer, primary_key=True, index=True)
    ac_status = Column(Boolean, nullable=False)
    temperature = Column(Float, nullable=True)
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
