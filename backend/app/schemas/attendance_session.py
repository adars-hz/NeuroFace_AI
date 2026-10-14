
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AttendanceSessionStart(BaseModel):
    assignment_id: int = Field(gt=0)
    duration_minutes: int = Field(default=60, ge=1, le=180)


class AttendanceSessionResponse(BaseModel):
    id: int
    assignment_id: int
    started_at: datetime
    expires_at: datetime
    ended_at: datetime | None
    status: Literal["ACTIVE", "CLOSED", "EXPIRED"]

    model_config = {"from_attributes": True}
