
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AttendanceRecordCreate(BaseModel):
    session_id: int = Field(gt=0)
    student_id: int = Field(gt=0)
    status: Literal["PRESENT", "ABSENT", "LEAVE"] = "PRESENT"


class AttendanceRecordResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: Literal["PRESENT", "ABSENT", "LEAVE"]
    marked_at: datetime
    marked_by: int

    model_config = {"from_attributes": True}
