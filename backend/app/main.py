
from fastapi import FastAPI

from app.core.config import APP_NAME
from app.api.users import router as users_router
from app.api.auth import router as auth_router

from app.api.students import router as students_router
from app.api.teachers import router as teachers_router
from app.api.classrooms import router as classrooms_router
from app.api.departments import router as departments_router
from app.api.subjects import router as subjects_router

app = FastAPI(title=APP_NAME)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(departments_router)
app.include_router(classrooms_router)
app.include_router(students_router)
app.include_router(teachers_router)
app.include_router(subjects_router)


@app.get("/")
def root():
    return {"message": "NeuroFace AI Backend is running"}