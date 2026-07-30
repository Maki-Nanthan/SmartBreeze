from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator


class ManualControlRequest(BaseModel):
    student_count: int | None = Field(default=None, ge=0)
    ac_status: bool | None = None
    temperature: float | None = Field(default=None, ge=16.0, le=35.0)

    @model_validator(mode="after")
    def validate_payload(self) -> Self:
        if self.student_count is None and self.ac_status is None and self.temperature is None:
            raise ValueError("At least one manual control field must be provided")
        return self
