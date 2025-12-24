import logging
from fastapi import APIRouter, HTTPException, status, Query
from config import settings
from backend.literature.service import LiteratureService

from backend.ideas.service import IdeaService


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_router = APIRouter(tags=["LS API Services"])
literature_service = LiteratureService()

idea_service = IdeaService()


from base_requests import GenerateRequest, GenerateResponse, IdeaRequest, IdeaResponse
from test_run import generate_summary


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
    Stable endpoint behind prefix: POST {settings.API_V1_STR}/generate

    Returns JSON in this shape:
    {
      "originalQuestion": "...",
      "providerUsed": "mistral | gemini | local | unknown",
      "usedLocalLLM": false,
      "answer": "final response text"
    }
    """
    try:
        logger.info("Generating content for question: %s", request.question)

        # Determine providerUsed string for the response
        provider_used = "local" if request.local_llm else (request.provider or "unknown")

        # Call generate_summary and pass the explicit provider
        result = generate_summary(text=request.question, local_llm=request.local_llm, provider=request.provider)

        if result is None:
            logger.error("LLM returned no result for question: %s", request.question)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM returned no response",
            )

        # Accept either dict or str from generate_summary (defensive)
        answer_text = ""
        if isinstance(result, str):
            answer_text = result.strip()
        elif isinstance(result, dict):
            answer_text = (
                result.get("answer")
                or result.get("summary")
                or result.get("text")
                or result.get("data")
                or ""
            )
            # If provider included in dict, prefer it for providerUsed
            provider_from_result = result.get("provider")
            if provider_from_result:
                provider_used = provider_from_result
        else:
            answer_text = str(result)

        if not answer_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM returned an empty answer",
            )

        response = GenerateResponse(
            originalQuestion=request.question,
            providerUsed=str(provider_used),
            usedLocalLLM=bool(request.local_llm),
            answer=answer_text,
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

    Returns:
      {
        "papers": [
          {"title": "...", "summary": "...", "year": 202X},
          ...
        ]
      }
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
    response_model=IdeaResponse,
    tags=["LS API Services"]
)
def idea_generation(request: IdeaRequest):
    ideas = idea_service.generate(
        domain=request.domain,
        venues=request.venues,
        papers=request.papers,
    )
    return {"ideas": ideas}