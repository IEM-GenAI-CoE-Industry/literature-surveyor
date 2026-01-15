import requests
import time
import logging

logger = logging.getLogger(__name__)

def search_venues_s2(domain: str):
    """
    Fetches venues by searching recent papers in Semantic Scholar.
    Returns: {"conferences": [], "journals": []} or None on error.
    """
    # S2 doesn't have a direct venue search, so we search papers and extract venues
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": domain,
        "limit": 10,
        "fields": "venue,publicationVenue"
    }
    
    venues = {"conferences": [], "journals": []}
    
    try:
        # 1-second delay to respect unauthenticated rate limits
        time.sleep(1) 
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 429:
            logger.warning("Semantic Scholar Rate Limit hit.")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        paper_list = data.get("data", [])
        seen_names = set()

        for paper in paper_list:
            # Try to get the full venue object first, then the simple string
            pub_venue = paper.get("publicationVenue")
            venue_name = paper.get("venue")
            
            # Prefer the detailed object name
            final_name = pub_venue.get("name") if pub_venue else venue_name
            
            if not final_name or final_name in seen_names:
                continue
                
            seen_names.add(final_name)
            
            # Simple heuristic to classify
            name_lower = final_name.lower()
            if any(x in name_lower for x in ["conference", "symposium", "workshop", "proc", "cvpr", "icml", "neurips", "aaai"]):
                venues["conferences"].append(final_name)
            else:
                # Default to journal/other
                venues["journals"].append(final_name)

        return venues

    except Exception as e:
        logger.error(f"Semantic Scholar Venue Error: {e}")
        return None