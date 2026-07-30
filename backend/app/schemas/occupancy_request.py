from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.schemas.classroom_state import OccupancyLevel


class OccupancyRequest(BaseModel):
    student_count: int | None = Field(default=None, ge=0)
    occupancy_level: OccupancyLevel | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "OccupancyRequest":
        if self.occupancy_level is None and self.student_count is None:
            raise ValueError("Either occupancy_level or student_count must be provided")
        return self
