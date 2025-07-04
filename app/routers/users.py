# app/routers/users.py
from fastapi import APIRouter, status, Depends, BackgroundTasks, HTTPException
from typing import List
from app.db.supabase import supabase
from app.schemas import user as user_schema
from app.services.matching_service import run_matching_process
from postgrest.exceptions import APIError

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

@router.post(
    "/search/{user_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a background search for a user",
    description="Initiates a background task to find matches for a specific user. This should be called by the frontend after a user has been created directly in Supabase."
)
def trigger_search_for_user(
    user_id: int,  # CHANGED: The user_id is now an integer
    background_tasks: BackgroundTasks
):
    """
    Triggers the AI matching process for an existing user.
    """
    try:
        # Step 1: Fetch the source user's data from the database.
        # CHANGED: Selecting 'description' field.
        # CHANGED: Using the integer 'user_id' directly in the query.
        response = supabase.table("users").select("id, description").eq("id", user_id).single().execute()
        user = response.data

    except APIError as e:
        if "PGRST116" in e.message:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' was not found in the database."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"A database API error occurred: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
    
    # Step 2: Add the matching process to the background.
    # CHANGED: Passing the 'description' field instead of 'story_paragraph'.
    background_tasks.add_task(
        run_matching_process,
        user_id=user['id'],
        user_description=user['description']
    )
    
    # Step 3: Return an immediate success response.
    return {"status": "accepted", "message": "Match search has been initiated in the background."}
