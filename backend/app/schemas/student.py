
from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    student_id: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=1, max_length=100)
    class_name: str = Field(min_length=1, max_length=50)


class StudentResponse(BaseModel):
    id: int
    user_id: int
    student_id: str
    full_name: str
    class_name: str
    face_registered: str

    model_config = {"from_attributes": True}
