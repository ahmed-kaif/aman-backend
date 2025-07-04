import google.generativeai as genai
import json
import logging
from typing import List, Dict
from app.core.config import settings
from app.db.supabase import supabase

# --- Gemini AI Model Configuration ---

# Configure the library with your API key
genai.configure(api_key=settings.GOOGLE_API_KEY)
# Initialize the model
model = genai.GenerativeModel("gemini-1.5-flash") # Using 1.5-flash as it's great for this task

# --- Logger Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_prompt(paragraph1: str, paragraph2: str) -> str:
    # This is the detailed prompt you provided, ensuring the AI has the right context.
    return f"""
You are an advanced AI system specialized in family reunification for refugees and displaced people from crisis zones including Gaza, Palestine, Syria, Sudan, Rohingya communities, Afghanistan, Ukraine, and other conflict areas.

CRITICAL MISSION: Analyze two user-submitted paragraphs to determine if they represent potential family connections. Lives depend on accurate matching.

PARAGRAPH 1: {paragraph1}
PARAGRAPH 2: {paragraph2}

COMPREHENSIVE ANALYSIS FRAMEWORK:

🔍 IDENTITY MARKERS (High Weight):
- Names: Full names, nicknames, diminutives, phonetic variants, transliterations
- Family relationships: Parent/child, siblings, spouses, extended family
- Physical descriptions: Age, height, scars, birthmarks, disabilities, clothing
- Personal items: Jewelry, documents, photos, distinctive belongings

🏠 LOCATION INTELLIGENCE (High Weight):
- Origin locations: Cities, villages, neighborhoods, districts, streets
- Current/last known locations: Refugee camps, shelters, host communities
- Transit routes: Checkpoints, borders, hospitals, evacuation centers
- Geographic landmarks: Schools, mosques, markets, specific buildings

⏰ TEMPORAL CORRELATIONS (Medium Weight):
- Separation dates: Exact dates, relative timeframes, seasonal references
- Event timing: Bombings, raids, evacuations, natural disasters
- Personal timelines: Ages at separation, anniversary dates, holidays

🎯 SITUATIONAL CONTEXT (Medium Weight):
- Separation events: Military operations, checkpoints, hospital visits, evacuations
- Circumstances: Chaos, forced movement, medical emergencies, detention
- Shared experiences: Same incident, similar routes, common destinations

🧬 RELATIONSHIP PATTERNS (Medium Weight):
- Complementary searches: One seeking parent, another seeking child
- Mutual descriptions: Physical traits, clothing, belongings matching
- Consistent timelines: Events aligning from different perspectives
- Family structure: Number of family members, ages, gender distribution

🗣️ LINGUISTIC CLUES (Low Weight):
- Dialectal similarities: Regional speech patterns, local terminology
- Cultural references: Religious practices, traditions, community customs
- Educational background: Literacy levels, language proficiency

⚡ ADVANCED MATCHING LOGIC:
- Account for trauma-induced memory gaps or inconsistencies
- Consider language barriers and translation errors
- Recognize cultural naming conventions and variations
- Factor in children's limited information or confused recollections
- Evaluate indirect connections (seeking same person from different relationships)

SCORING CRITERIA:
- 0.9-1.0: Almost certain match (multiple strong indicators align)
- 0.7-0.89: Strong probability (several key markers match with minor discrepancies)
- 0.5-0.69: Moderate possibility (some significant similarities but missing key confirmations)
- 0.3-0.49: Weak connection (few similarities, mostly circumstantial)
- 0.0-0.29: Unlikely match (minimal or no meaningful connections)

SPECIAL CONSIDERATIONS:
- Prioritize exact name matches with location/time correlation
- Weight parent-child relationships higher than distant relatives
- Consider age progression for long-term separations
- Account for nickname/formal name variations
- Recognize possible gender confusion in translated texts
- Factor in trauma-induced memory alterations

Return ONLY this JSON format:

```json
{{
  "similarity_score": [0.00-1.00]
}}
No explanations, analysis, or additional fields. Only the similarity_score as a precise decimal between 0.0 and 1.0.
"""

def get_similarity_score(paragraph1: str, paragraph2: str) -> float:
    """Calls the Gemini API and robustly parses the JSON response."""
    if not paragraph1 or not paragraph2:
        return 0.0
    prompt = build_prompt(paragraph1, paragraph2)
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean the response to extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.rfind("```")
            response_text = response_text[json_start:json_end].strip()
        
        response_json = json.loads(response_text)
        score = float(response_json.get("similarity_score", 0.0))
        logger.info(f"Successfully calculated similarity score: {score}")
        return score

    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.error(f"Failed to parse AI response: {e}\nRaw response: '{response.text}'")
        return 0.0
    except Exception as e:
        logger.error(f"An unexpected error occurred during AI call: {e}")
        return 0.0

def find_and_store_top_matches(new_user_id: int, new_user_paragraph: str):
    """
    Finds top 10 matches for a new user and saves them to the database.
    This function is designed to be run in the background.
    """
    logger.info(f"Starting matching process for new user: {new_user_id}")
    # 1. Fetch all other users from the database
    try:
        response = supabase.table("users").select("id, description").neq("id", new_user_id).execute()
        existing_users = response.data
        if not existing_users:
            logger.info("No other users in the database to match against.")
            return
    except Exception as e:
        logger.error(f"Failed to fetch existing users from Supabase: {e}")
        return

    # 2. Calculate similarity scores for each user
    all_matches = []
    for user in existing_users:
        logger.info(f"Matching new user against existing user: {user['id']}")
        score = get_similarity_score(new_user_paragraph, user['description'])
        if score > 0.29: # Only consider scores above "Unlikely match"
            all_matches.append({"id": user['id'], "score": score})

    # 3. Sort by score and get the top 10
    sorted_matches = sorted(all_matches, key=lambda x: x['score'], reverse=True)
    top_10_matches = sorted_matches[:10]

    logger.info(f"Found {len(top_10_matches)} potential matches for user {new_user_id}.")

    # 4. Prepare data for batch insertion
    if not top_10_matches:
        return

    matches_to_insert = [
        {
            "user1_id": new_user_id,
            "user2_id": match['id'],
            "match_score": match['score']
        }
        for match in top_10_matches
    ]

# 5. Insert top matches into the 'matches' table
    try:
        supabase.table("matches").insert(matches_to_insert).execute()
        logger.info(f"Successfully stored {len(matches_to_insert)} matches in the database.")
    except Exception as e:
        logger.error(f"Failed to insert matches into Supabase: {e}")

def run_matching_process(user_id: int, user_description: str):
    """
    High-level background task. It now uses a try/finally block to ensure
    the 'is_processed' flag is always updated to True upon completion.
    """
    logger.info(f"--- BG TASK: START for user {user_id} ---")
    try:
        # Step 1: Clear any pre-existing matches for this user.
        logger.info(f"Clearing old matches for source_user_id: {user_id}")
        supabase.table("matches").delete().eq("user1_id", user_id).execute()
        # currently processing
        supabase.table("users").update({"is_processed": 0}).eq("id", user_id).execute()

        # Step 2: Find and store the new top matches.
        find_and_store_top_matches(new_user_id=user_id, new_user_paragraph=user_description)

    except Exception as e:
        logger.error(f"BG TASK: An error occurred for user {user_id}: {e}")
        
    finally:
        # NEW: This block will ALWAYS run, whether the 'try' block succeeded or failed.
        # This is crucial for preventing users from getting stuck in a processing state.
        logger.info(f"BG TASK: FINISHING for user {user_id}. Setting is_processed to True.")
        try:
            supabase.table("users").update({"is_processed": 1}).eq("id", user_id).execute()
            logger.info(f"BG TASK: Successfully marked user {user_id} as processed.")
        except Exception as e:
            logger.error(f"BG TASK: CRITICAL - FAILED to mark user {user_id} as processed: {e}")
    logger.info(f"--- BG TASK: COMPLETE for user {user_id} ---")
