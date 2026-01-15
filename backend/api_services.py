import logging
from fastapi import APIRouter, HTTPException, status
from config import settings

# --- IMPORT VENUE DISCOVERY SERVICE ---
from venue_discovery.service import discover_venues

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_router = APIRouter(tags=["LS API Services"])

from base_requests import GenerateRequest, GenerateResponse
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
    """
    try:
        logger.info("Generating content for question: %s", request.question)

        # Determine providerUsed string for the response
        provider_used = "local" if request.local_llm else (request.provider or "unknown")

        # --- PHASE 3: ACADEMIC VENUE DISCOVERY ---
        # 1. Discover venues based on the user question (acting as domain)
        venues_data = discover_venues(request.question)
        
        # 2. Format venues to pass to the LLM (Context Injection)
        # We format this as a string to append to the system prompt context
        venues_context = "\n\n[CONTEXT: ACADEMIC VENUES FOUND]\n"
        venues_context += f"Conferences: {', '.join(venues_data.get('conferences', []))}\n"
        venues_context += f"Journals: {', '.join(venues_data.get('journals', []))}\n"
        
        logger.info(f"Injecting Venue Context: {venues_context.strip()}")
        
        # 3. Enhance the input text sent to the LLM
        # We append the discovered context so the LLM knows about these venues
        enhanced_input = request.question + venues_context

        # --- CALL EXISTING LLM LOGIC ---
        result = generate_summary(text=enhanced_input, local_llm=request.local_llm, provider=request.provider)

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