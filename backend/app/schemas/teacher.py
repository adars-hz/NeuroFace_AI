
from typing import Literal
from pydantic import BaseModel, Field


class TeacherCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    employee_id: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=1, max_length=100)
    designation: Literal["TEACHER", "HOD"] = "TEACHER"


class TeacherResponse(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: str
    designation: str

    model_config = {"from_attributes": True}
