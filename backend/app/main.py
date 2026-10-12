
from fastapi import FastAPI

from app.core.config import APP_NAME
from app.api.users import router as users_router

app = FastAPI(title=APP_NAME)

app.include_router(users_router)


@app.get("/")
def root():
    return {"message": "NeuroFace AI Backend is running"}