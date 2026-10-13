
from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    department_code: str = Field(min_length=2, max_length=20)
    department_name: str = Field(min_length=2, max_length=100)


class DepartmentResponse(BaseModel):
    id: int
    department_code: str
    department_name: str

    model_config = {"from_attributes": True}
