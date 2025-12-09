import logging
from fastapi import APIRouter, HTTPException, status
from config import settings

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
