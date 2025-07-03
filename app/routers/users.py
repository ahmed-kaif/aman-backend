# app/routers/users.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.db.supabase import supabase
from app.schemas import user as user_schema

router = APIRouter()

@router.post("/", response_model=user_schema.User, status_code=201)
def create_user(user_in: user_schema.UserCreate):
    """
    Create a new user in the Supabase 'users' table.
    """
    # Convert Pydantic model to dict, ensuring URLs are strings
    user_data = user_in.model_dump(mode='json')
    
    response = supabase.table("users").insert(user_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not create user.")
    
    created_user = response.data[0]
    return created_user


@router.get("/{user_id}", response_model=user_schema.User)
def read_user(user_id: int):
    """
    Retrieve a single user by their ID.
    """
    response = supabase.table("users").select("*").eq("id", user_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
        
    return response.data


@router.get("/", response_model=List[user_schema.User])
def read_users(skip: int = 0, limit: int = 100):
    """
    Retrieve a list of users.
    """
    response = supabase.table("users").select("*").range(skip, skip + limit - 1).execute()

    if not response.data:
        return [] # Return empty list if no users found
        
    return response.data
