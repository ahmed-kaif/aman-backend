# app/main.py
from fastapi import FastAPI, Request, status
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

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(req: Request):
    root_path = req.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title="API",
    )
@app.get("/healthz", include_in_schema=False)
async def check_api_health():
    return {"status": "OK"}
# Include the users router
app.include_router(
    users.router, 
    prefix=f"{settings.API_V1_STR}/users", 
    tags=["Users"]
)
