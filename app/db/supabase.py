# app/db/supabase.py
from supabase import create_client, Client
from app.core.config import settings

# Initialize the Supabase client
supabase: Client = create_client(
    supabase_url=str(settings.SUPABASE_URL),
    supabase_key=settings.SUPABASE_KEY
)
