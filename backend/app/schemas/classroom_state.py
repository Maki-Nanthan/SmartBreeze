from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import AliasChoices, BaseModel, Field


class OccupancyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ControlMode(str, Enum):
    AI_SIMULATION = "AI_SIMULATION"
    MANUAL = "MANUAL"
    EDGE_AI = "EDGE_AI"


class ClassroomState(BaseModel):
    student_count: int = Field(default=0, ge=0)
    occupancy_level: OccupancyLevel = OccupancyLevel.LOW
    ac_status: bool = False
    temperature: float | None = Field(default=None, ge=16.0, le=35.0)
    control_mode: ControlMode = ControlMode.AI_SIMULATION
    timestamp: datetime = Field(validation_alias=AliasChoices("timestamp", "last_updated"))

    model_config = {"populate_by_name": True, "populate_by_alias": True}
