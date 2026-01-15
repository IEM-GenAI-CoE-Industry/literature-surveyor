from .mock_data import get_mock_venues
from .openalex_provider import search_venues_openalex
from .semantic_scholar import search_venues_s2
import logging

logger = logging.getLogger(__name__)

def discover_venues(domain: str):
    """
    Phase 3 Main Logic:
    1. Query OpenAlex
    2. Query Semantic Scholar
    3. Merge & Deduplicate
    4. Fallback to Mock Data if needed
    """
    logger.info(f" Phase 3: Discovering venues for '{domain}'...")
    
    combined_venues = {
        "conferences": set(),
        "journals": set()
    }
    
    providers_successful = False

    # --- Step 1: Query OpenAlex ---
    oa_data = search_venues_openalex(domain)
    if oa_data:
        # Check if we actually got results
        if oa_data["conferences"] or oa_data["journals"]:
            providers_successful = True
            combined_venues["conferences"].update(oa_data["conferences"])
            combined_venues["journals"].update(oa_data["journals"])

    # --- Step 2: Query Semantic Scholar ---
    s2_data = search_venues_s2(domain)
    if s2_data:
        if s2_data["conferences"] or s2_data["journals"]:
            providers_successful = True
            combined_venues["conferences"].update(s2_data["conferences"])
            combined_venues["journals"].update(s2_data["journals"])

    # --- Step 3: Merge & Format ---
    final_result = {
        "conferences": sorted(list(combined_venues["conferences"]))[:5], # Top 5
        "journals": sorted(list(combined_venues["journals"]))[:5]        # Top 5
    }

    # --- Step 4: Fallback ---
    # If no APIs worked or results are empty, use mock data
    if not providers_successful or (not final_result["conferences"] and not final_result["journals"]):
        logger.warning(" APIs failed or returned no venues. Using Mock Data.")
        return get_mock_venues(domain)

    logger.info(f" Found {len(final_result['conferences'])} conferences and {len(final_result['journals'])} journals.")
    return final_result