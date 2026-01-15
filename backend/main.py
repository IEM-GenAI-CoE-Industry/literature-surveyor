from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import sys
import os

# --- PATH SETUP ---
# Ensure backend folder is in python path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORTS ---
try:
    # Import the Phase 3 Service logic
    from venue_discovery.service import discover_venues
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import 'venue_discovery'. check folders. Details: {e}")
    # Fallback to prevent crash during development
    def discover_venues(domain):
        return {"conferences": [], "journals": [], "error": "Import Failed"}

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("LiteratureSurveyor")

# --- INITIALIZE APP ---
app = FastAPI(
    title="Literature Surveyor API",
    description="Prototype API for Academic Venue Discovery & Idea Generation",
    version="1.0.0"
)

# --- DATA MODELS ---
class GenerateRequest(BaseModel):
    text: str
    mode: Optional[str] = "comprehensive"

# --- API ENDPOINTS ---

@app.get("/")
def health_check():
    """Simple check to see if server is running."""
    return {"status": "Literature Surveyor API is online"}

@app.post("/LS/content/v1/generate")
async def generate_content(request: GenerateRequest):
    """
    SECTION 1A: Main Service — Generate
    -----------------------------------
    1. Receives user question/domain
    2. Phase 2: Input Normalization
    3. Phase 3: Academic Venue Discovery
    4. Returns structured summary
    """
    logger.info(f"Received Request: '{request.text}'")

    # =========================================================
    # PHASE 2: INPUT NORMALIZATION & RESEARCH INTENT
    # =========================================================
    logger.info("--- Executing Phase 2: Input Normalization ---")
    
    # 1. Normalize Text: Lowercase and strip whitespace
    normalized_text = request.text.strip().lower()
    
    # 2. Heuristic Scope Detection
    # If query is 2 words or less (e.g., "machine learning"), it's Broad.
    # If longer (e.g., "machine learning for cancer detection"), it's Narrow.
    word_count = len(normalized_text.split())
    scope = "broad" if word_count <= 2 else "narrow"
    
    # 3. Create Structured Intent Object
    research_intent = {
        "domain": normalized_text,
        "subdomain": None,
        "scope": scope
    }
    logger.info(f"Phase 2 Complete. Intent: {research_intent}")

    # =========================================================
    # PHASE 3: ACADEMIC VENUE DISCOVERY
    # =========================================================
    logger.info("--- Executing Phase 3: Venue Discovery ---")
    
    # Call the helper module we created in venue_discovery/service.py
    # We pass the CLEANED domain from Phase 2
    venues_result = discover_venues(research_intent["domain"])
    
    # =========================================================
    # RETURN STRUCTURED RESPONSE (Step 7)
    # =========================================================
    return {
        "status": "success",
        "phases_completed": ["Phase 2 (Normalization)", "Phase 3 (Venue Discovery)"],
        "research_intent": research_intent,
        "step_3_venues": venues_result
    }