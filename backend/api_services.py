import logging
from fastapi import APIRouter, HTTPException, status, Query
# from config import settings # Ensure this file exists, otherwise comment out
from literature.service import LiteratureService
from ideas.service import IdeaService
from quality_filter.relevance_filter import quality_filter

# --- IMPORT VENUE DISCOVERY SERVICE ---
from venue_discovery.service import discover_venues

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_router = APIRouter(tags=["LS API Services"])

# Import data models (Ensure these exist in base_requests.py)
from base_requests import GenerateRequest, GenerateResponse
# Assuming IdeaRequest/IdeaResponse are also in base_requests or similar
try:
    from base_requests import IdeaRequest, IdeaResponse
except ImportError:
    # Fallback if not defined yet
    from pydantic import BaseModel
    class IdeaRequest(BaseModel):
        domain: str
        venues: list
        papers: list
    class IdeaResponse(BaseModel):
        ideas: list

from test_run import generate_summary

# --- INSTANTIATE SERVICES ---
literature_service = LiteratureService()
idea_service = IdeaService()

@api_router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid Question"},
        422: {"description": "Unprocessable Question"},
    },
)
async def generate_content(request: GenerateRequest) -> GenerateResponse:
    """
    Full pipeline endpoint behind prefix: POST {settings.API_V1_STR}/generate

    Pipeline steps implemented here:
      - Phase 2: Input normalization (lightweight normalization)
      - Phase 3: Venue discovery (discover_venues)
      - Phase 4: Literature retrieval (literature_service.fetch)
      - Phase 5: Idea generation (idea_service.generate)
      - Phase 6: Assemble a structured `answer` string for frontend rendering
    """
    try:
        logger.info("Generating content for question: %s", request.question)

        # Phase 2: normalize input
        domain_raw = (request.question or "").strip()
        domain = domain_raw.lower()

        # Phase 3: discover venues
        try:
            venues_data = discover_venues(domain)
        except Exception:
            logger.exception("Venue discovery failed; continuing with empty venues")
            venues_data = {"conferences": [], "journals": []}

        conferences = venues_data.get("conferences", []) or []
        journals = venues_data.get("journals", []) or []
        # Format conf_str and jour_str: comma-joined or 'None'
        conf_str = ", ".join(conferences[:5]) if conferences else "None"
        jour_str = ", ".join(journals[:5]) if journals else "None"

        # Phase 4: literature (fetch 5)
        try:
            papers = literature_service.fetch(domain, limit=5)
        except Exception:
            logger.exception("Literature retrieval failed; using fallback")
            try:
                papers = literature_service.fetch("", limit=5)
            except Exception:
                papers = []

        if not isinstance(papers, list):
            papers = []
        papers = papers[:5]

        # Helper: truncate to 400 chars for paper summaries
        def truncate(text: str, max_chars: int = 400) -> str:
            if not text:
                return ""
            s = str(text).strip()
            if len(s) <= max_chars:
                return s
            t = s[: max_chars - 3]
            if " " in t:
                t = t.rsplit(" ", 1)[0]
            return t + "..."

        # Build papers_text with single newlines between papers
        papers_lines = []
        for idx, p in enumerate(papers, start=1):
            if not isinstance(p, dict):
                title = str(p)
                summary = ""
                source = "OpenAlex"
                year = ""
            else:
                title = p.get("title") or p.get("paper_title") or "Untitled"
                summary = p.get("summary") or p.get("abstract") or ""
                source = p.get("source") or p.get("venue") or p.get("journal") or p.get("conference") or "OpenAlex"
                year = str(p.get("year") or p.get("pub_year") or "")

            papers_lines.append(f"{idx}) Title: {title}")
            papers_lines.append(f"   Summary: {truncate(summary, max_chars=400)}")
            papers_lines.append(f"   Source: {source} | Year: {year}")

        papers_text = "\n".join(papers_lines) if papers_lines else "No papers found."

    # Phase 5: idea generation
        try:
            ideas = idea_service.generate(domain=domain, venues=list(dict.fromkeys(conferences + journals)), papers=papers) or []
        except Exception:
            logger.exception("Idea generation failed; using fallback")
            try:
                ideas = idea_service.generate(domain=domain, venues=[], papers=[]) or []
            except Exception:
                ideas = []

        # Ensure exactly 5 ideas and format as numbered list '1. Idea'
        ideas_list = (ideas or [])[:5]
        while len(ideas_list) < 5:
            ideas_list.append("(no idea generated)")
        ideas_lines = [f"{i}. {' '.join(str(ideas_list[i-1]).split())}" for i in range(1, 6)]
        ideas_text = "\n".join(ideas_lines)

        # Phase 6: overview (single, short sentence under 30 words requested of the LLM)
        overview_prompt = f"Write a single, short sentence under 30 words summarizing the domain, discovered venues, and example papers for '{domain}'."
        overview_text = ""
        try:
            ov = generate_summary(text=overview_prompt, local_llm=getattr(request, "local_llm", False), provider=getattr(request, "provider", "unknown"))
            if isinstance(ov, dict):
                overview_text = ov.get("answer") or ov.get("summary") or ov.get("text") or ""
            elif isinstance(ov, str):
                overview_text = ov
            else:
                overview_text = str(ov)
        except Exception:
            logger.exception("Overview generation failed")
            overview_text = ""

        # Do not truncate the overview; rely on LLM prompt to keep it short
        overview_text = overview_text.strip()

        # Assembly: exact template requested
        # Build structured papers list for JSON output (ensure required fields)
        papers_struct = []
        for p in papers:
            if not isinstance(p, dict):
                papers_struct.append({
                    "title": str(p),
                    "summary": "",
                    "year": "",
                    "source": "OpenAlex",
                    "cited_by_count": 0,
                })
            else:
                # Ensure cited_by_count is an integer (OpenAlex uses 'cited_by_count')
                cited_raw = p.get("cited_by_count") if p.get("cited_by_count") is not None else p.get("cited_by")
                try:
                    cited_val = int(cited_raw or 0)
                except Exception:
                    cited_val = 0
                papers_struct.append({
                    "title": p.get("title") or p.get("paper_title") or "Untitled",
                    "summary": p.get("summary") or p.get("abstract") or "",
                    "year": p.get("year") or p.get("pub_year") or "",
                    "source": p.get("source") or p.get("venue") or p.get("journal") or p.get("conference") or "OpenAlex",
                    "cited_by_count": cited_val,
                })

        answer = (
            f"Input Domain: {domain}\n\n"
            f"Discovered Venues:\n"
            f"Conferences: {conf_str}\n"
            f"Journals: {jour_str}\n\n"
            f"Example Papers:\n"
            f"{papers_text}\n\n"
            f"Research Ideas:\n"
            f"{ideas_text}\n\n"
            f"Overview:\n"
            f"{overview_text}"
        )

        structured = {
            "domain": domain,
            "overview": overview_text,
            "venues": {"conferences": conferences[:5], "journals": journals[:5]},
            "papers": papers_struct,
            "ideas": ideas_list[:5],
        }

        response = GenerateResponse(
            originalQuestion=request.question,
            providerUsed=str(getattr(request, "provider", "unknown")),
            usedLocalLLM=bool(getattr(request, "local_llm", False)),
            answer=answer,
            structured_data=structured,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error generating content")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating content: {str(e)}",
        )

def llm_call(prompt: str) -> str:
    return """
1. Stability Analysis of Hybrid Dynamical Systems
2. Control of Chaotic Oscillators Using Feedback
3. Learning-Based Reduced Order Models for PDEs
"""

print("registering /literature route")
@api_router.get("/literature", tags=["LS API Services"])
def literature_retrieval(
    q: str = Query(..., min_length=2, description="Search query for paper retrieval"),
    limit: int = Query(5, ge=3, le=5, description="Number of papers to return (3–5)"),
):
    """
    PHASE 4 — LITERATURE RETRIEVAL (LIMITED)
    """
    try:
        papers = literature_service.fetch(q, limit)
        return {"papers": papers}
    except Exception:
        # Hard fallback: never fail the pipeline
        return {"papers": literature_service.fetch("", limit)}


# ---------- PHASE 5 ----------
@api_router.post(
    "/ideas",
    # response_model=IdeaResponse, # Uncomment if IdeaResponse is imported
    tags=["LS API Services"]
)
def idea_generation(request: IdeaRequest):

    # -------- PHASE 4.5: QUALITY CONTROL --------
    filtered = quality_filter(
        domain=request.domain,
        venues=request.venues,
        papers=request.papers,
    )

    filtered_venues = filtered["filtered_venues"]
    filtered_papers = filtered["filtered_papers"]

    # -------- PHASE 5: IDEA GENERATION --------
    ideas = idea_service.generate(
        domain=request.domain,
        venues=filtered_venues,
        papers=filtered_papers,
    )

    return {"ideas": ideas}
# ...existing code...
# ...existing code...
