
from datetime import datetime

from pydantic import BaseModel


class FaceRegistrationResponse(BaseModel):
    id: int
    student_id: int
    image_path: str
    status: str
    registered_at: datetime

    model_config = {"from_attributes": True}
