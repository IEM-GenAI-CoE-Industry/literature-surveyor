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

# Import your custom modules
# We use try/except to ensure the app doesn't crash if config is slightly different,
# but normally this will import your existing files.
try:
    from api_services import api_router
    from config import settings
except ImportError:
    # Fallback/Placeholder if specific config files are missing in this context
    from fastapi import APIRouter
    api_router = APIRouter()
    class Settings:
        PROJECT_NAME = "Literature Surveyor"
        API_V1_STR = "/LS/content/v1"
    settings = Settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_tags=[
        {"name": "LS Platform Services", "description": "Literature Surveyor Platform APIs"}
    ],
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

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

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(root_router)

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