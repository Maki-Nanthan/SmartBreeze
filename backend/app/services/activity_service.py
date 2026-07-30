from __future__ import annotations

from enum import Enum


class ActivityType(str, Enum):
    JANITOR_CLEANING = "janitor_cleaning"
    STUDENT_ARRIVING = "student_arriving"
    STUDENT_LEAVING = "student_leaving"
