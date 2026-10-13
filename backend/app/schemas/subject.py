
from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    subject_code: str = Field(min_length=2, max_length=20)
    subject_name: str = Field(min_length=2, max_length=100)
    class_id: int = Field(gt=0)


class SubjectResponse(BaseModel):
    id: int
    subject_code: str
    subject_name: str
    class_id: int

    model_config = {"from_attributes": True}
