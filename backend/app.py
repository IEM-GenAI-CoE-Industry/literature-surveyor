import sys
from pathlib import Path

# Add parent directory to path to allow importing from config and api_services
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from typing import Any
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import logging

# Import your custom modules directly. If these imports fail the traceback will
# be shown and the process will exit so the root cause is visible (no silent fallback).
from api_services import api_router
from config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_tags=[
        {"name": "LS Platform Services", "description": "Literature Surveyor Platform APIs"}
    ],
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Simple logger to surface route registration at startup
logger = logging.getLogger("backend_app")


# --- PERMANENT CORS FIX ---
# Instead of listing specific ports (like ["http://localhost:5175"]), 
# we use a Regex to allow ANY port on localhost.
# This fixes the issue where Vite switches to port 5176 or 5177.
app.add_middleware(
    CORSMiddleware,
    # This Regex allows http://localhost or http://127.0.0.1 on ANY port
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?", 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------

root_router = APIRouter()

@root_router.get("/")
def index(request: Request) -> Any:
    """Basic HTML response."""
    body = (
        "<html>"
        "<body style='padding: 10px;'>"
        "<h1>Literature Surveyor Platform APIs</h1>"
        "<div>"
        "Check the API spec: <a href='/docs'>here</a>"
        "</div>"
        "</body>"
        "</html>"
    )
    return HTMLResponse(content=body)


@root_router.get("/health")
def health() -> Any:
    """Simple health-check for automated checks and frontend readiness probes."""
    return {"status": "ok"}

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(root_router)


@app.on_event("startup")
async def _log_registered_routes():
    # Print registered routes to help diagnose 404s when api_router failed to import
    try:
        registered = [r.path for r in app.routes]
        logger.info(f"Registered routes: {registered}")
        print("Registered routes:", registered)

        # Check whether any route exists under the API prefix
        api_prefixed = [p for p in registered if p.startswith(settings.API_V1_STR)]
        if not api_prefixed:
            logger.warning(f"No routes found under prefix {settings.API_V1_STR}. This often happens when api_services failed to import. Check the server log for ImportError trace.")
            print(f"WARNING: No routes found under prefix {settings.API_V1_STR}. api_services may have failed to import.")
    except Exception:
        # Avoid failing startup just for logging
        pass

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8001
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=300,
        log_level="info",
    )