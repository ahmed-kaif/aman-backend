# app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.routers import users
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
# Define a list of allowed origins.
# For development, you can allow all origins with ["*"]
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
