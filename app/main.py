# app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.routers import users

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME}"}

# Include the users router
app.include_router(
    users.router, 
    prefix=f"{settings.API_V1_STR}/users", 
    tags=["Users"]
)
