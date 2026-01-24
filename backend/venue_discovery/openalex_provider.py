import requests
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup Logging
logger = logging.getLogger(__name__)

# --- Load Environment Variables ---
# Explicitly look for the .env file in the backend folder
# (Assuming this file is in backend/venue_discovery/)
env_path = Path(__file__).resolve().parent.parent / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    # logger.info("OpenAlex Provider: .env loaded successfully.")

def search_venues_openalex(domain: str):
    """
    Fetches venues from OpenAlex by searching for WORKS (Papers) first,
    then extracting the journals/conferences they appear in.
    """
    # Use /works to find papers about the topic
    url = "https://api.openalex.org/works"
    
    # 1. Get Email from loaded .env
    email = os.getenv("EMAIL")
    
    # 2. Prepare Parameters
    params = {
        "search": domain,
        "per_page": 60, # Fetch 60 impactful papers to get a good mix of venues
        "sort": "cited_by_count:desc" # Sort by impact to get top-tier venues
    }
    
    # 3. Add Email for Polite Pool (Speed Boost) if it exists
    if email:
        params["mailto"] = email
    else:
        logger.warning("OpenAlex: No EMAIL found in .env. Running in slow mode.")
    
    # Header user-agent is good practice, but 'mailto' param is the critical one for OpenAlex
    headers = {}
    if email:
        headers["User-Agent"] = f"LiteratureSurveyor/1.0 (mailto:{email})"
    
    venues = {"conferences": [], "journals": []}
    seen_names = set()
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        
        for item in results:
            # Extract the Venue (Source) from the paper metadata
            primary_loc = item.get("primary_location") or {}
            source = primary_loc.get("source")
            
            if not source:
                continue
                
            name = source.get("display_name")
            
            # Deduplicate
            if not name or name in seen_names: 
                continue
                
            seen_names.add(name)
            
            # Classify as Conference or Journal
            v_type = (source.get("type") or "").lower()
            
            if "conference" in v_type or "proceeding" in v_type:
                venues["conferences"].append(name)
            elif "journal" in v_type:
                venues["journals"].append(name)
            else:
                # Fallback heuristics based on name
                name_lower = name.lower()
                if any(x in name_lower for x in ["conf", "proc", "symposium", "workshop", "icml", "neurips", "cvpr"]):
                    venues["conferences"].append(name)
                else:
                    # Default others to journals
                    venues["journals"].append(name)
        
        # Limit to top 5 unique results per category
        venues["conferences"] = venues["conferences"][:5]
        venues["journals"] = venues["journals"][:5]
                    
        return venues

    except Exception as e:
        logger.error(f"OpenAlex Venue Error: {e}")
        return None
    
    # --- TEST BLOCK (Add this to the end of the file) ---
if __name__ == "__main__":
    # This allows you to run the file directly to test it
    test_topic = input("Enter a topic to test (e.g. Deep Learning): ") or "Machine Learning"
    
    print(f"\n--- Testing OpenAlex Venue Discovery for: '{test_topic}' ---")
    results = search_venues_openalex(test_topic)
    
    if results:
        print("\nFound Conferences:")
        for conf in results.get("conferences", []):
            print(f" - {conf}")
            
        print("\nFound Journals:")
        for jour in results.get("journals", []):
            print(f" - {jour}")
    else:
        print("No results found or an error occurred.")