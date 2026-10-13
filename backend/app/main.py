
from fastapi import FastAPI

from app.core.config import APP_NAME
from app.api.users import router as users_router
from app.api.auth import router as auth_router

from app.api.students import router as students_router
from app.api.teachers import router as teachers_router

app = FastAPI(title=APP_NAME)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(students_router)
app.include_router(teachers_router)


@app.get("/")
def root():
    return {"message": "NeuroFace AI Backend is running"}