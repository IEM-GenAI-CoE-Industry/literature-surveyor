from util.llm_factory import get_llm
from util.system_prompt import LITERATURE_SYSTEM_PROMPT

from typing import Optional, Dict
import os
import logging

logger = logging.getLogger(__name__)


def _compose_message(system_prompt: str, user_question: str) -> str:
    """
    Compose a single text to send to the LLM. Many vendor wrappers accept a simple
    text input. We prepend the system prompt as requested.
    """
    # Ensure spacing and trimming
    system = (system_prompt or "").strip()
    user = (user_question or "").strip()
    if system and user:
        return f"{system}\n\nUser question:\n{user}"
    if user:
        return user
    return system


def generate_summary(text: str, local_llm: bool = False, provider: str | None = None, temperature: float = 0.7) -> Optional[Dict[str, str]]:
    """
    Generates a summary of the given text using the configured LLM.

    Returns:
      dict with {"provider": "<provider>", "answer": "<text>"} on success
      None on failure
    """
    if not text or not text.strip():
        return None

    # Compose the full prompt (system prompt + user question)
    combined = _compose_message(LITERATURE_SYSTEM_PROMPT, text)

    # Acquire the LLM instance (or clear error string)
    llm_or_error = get_llm(local_llm=local_llm, provider=provider, temperature=temperature)

    # If the factory returned a string, that's an error note for local_llm missing
    if isinstance(llm_or_error, str):
        # Return the error message as the 'answer' (so frontend shows it)
        chosen_provider = "local_error"
        return {"provider": chosen_provider, "answer": llm_or_error}

    # llm_or_error is assumed to be an object exposing invoke(...) method (vendor wrappers)
    try:
        # Try invoking. Some wrappers accept formatted messages, some accept raw text.
        # We'll first try to pass the combined text as-is and fall back to .invoke([messages]) if needed.
        response = None
        try:
            response = llm_or_error.invoke(combined)
        except TypeError:
            # Some wrappers expect a list of messages or formatted object. Try raw string as fallback
            response = llm_or_error.invoke(combined)
        except Exception as inner_e:
            # In case the wrapper uses .invoke with ChatPromptTemplate earlier, try to extract .content from the response
            logger.debug("Primary invoke raised: %s", inner_e)
            try:
                response = llm_or_error.invoke(combined)
            except Exception:
                raise

        # Extract textual content from common shapes
        summary_text = None
        if response is None:
            summary_text = None
        elif isinstance(response, str):
            summary_text = response
        elif isinstance(response, dict):
            summary_text = response.get("content") or response.get("answer") or response.get("text") or response.get("data")
        else:
            # vendor wrappers commonly return an object with .content or .text
            summary_text = getattr(response, "content", None) or getattr(response, "text", None) or str(response)

        if not summary_text:
            logger.error("LLM returned no textual content.")
            return None

        chosen_provider = "local" if local_llm else (provider or os.getenv("llm_provider", "unknown"))
        return {"provider": chosen_provider, "answer": summary_text.strip()}

    except Exception as e:
        logger.exception("Error calling LLM: %s", e)

        return {"provider": provider or os.getenv("llm_provider", "unknown"), "answer": f"Error invoking LLM: {e}"}

        
