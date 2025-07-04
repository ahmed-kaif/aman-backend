# app/core/config.py
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Aman ID"
    API_V1_STR: str = "/api/v1"
    SUPABASE_URL: AnyHttpUrl
    SUPABASE_KEY: str
    GOOGLE_API_KEY: str
    
    # To load environment variables from a .env file, uncomment the following line
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
