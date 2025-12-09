import os
import sys
from dotenv import load_dotenv

# ensure project root is on path so relative imports of langchain_* modules work
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)

# load .env once, but DO NOT override already-existing environment variables.
load_dotenv(override=False)

# Import vendor wrappers (may raise ImportError if not installed — we'll handle gracefully)
try:
    from langchain_mistralai import ChatMistralAI
except Exception:
    ChatMistralAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None

try:
    from langchain_groq import ChatGroq
except Exception:
    ChatGroq = None

# Ollama local model wrapper
try:
    from langchain_ollama import ChatOllama
except Exception:
    ChatOllama = None

# Optional prompt helpers — not required for get_llm but kept for parity
from typing import Optional, Union

import util.constants as constants


def _get_env_provider() -> str:
    """Return provider set in env (lowercased), or empty string if not set."""
    return os.getenv("llm_provider", "").strip().lower()


def get_llm(local_llm: bool = False, provider: Optional[str] = None, temperature: float = 0.3) -> Union[object, str]:
    """
    Returns an LLM instance configured according to arguments.

    Args:
      local_llm: if True, returns a local Ollama LLM instance.
      provider: explicit provider string ('mistral'|'gemini'|'openai'|'groq') to use when local_llm is False.
                If None, falls back to environment variable llm_provider.
      temperature: model temperature.

    Returns:
      - If successful: an LLM instance (object) with an `.invoke()` method expected by the rest of the code.
      - If local_llm was requested but Ollama is not available or misconfigured: a clear error string describing the problem.
      - If requested cloud provider is unsupported or missing dependencies: raises ValueError.
    """
    # LOCAL LLM branch
    if local_llm:
        # Check if Ollama wrapper is available
        if ChatOllama is None:
            return "Local Ollama model requested but Ollama wrapper (langchain_ollama) is not installed or importable."

        # require local_model_url env var or default to localhost
        base_url = os.getenv("local_model_url") or "http://localhost:11434"
        local_model_name = getattr(constants, "local_llm", None) or "ollama:llama2"  # fallback hint

        # If Ollama server likely not reachable, we can't know here — we return the instance and let invocation fail if server unreachable.
        try:
            return ChatOllama(model=local_model_name, base_url=base_url)
        except Exception as e:
            # Return a clear error string as requested
            return f"Local Ollama model configuration failed: {e}. Ensure Ollama server is running at {base_url} and a model named '{local_model_name}' is installed."

    # CLOUD LLM branch
    chosen = (provider or _get_env_provider() or "").strip().lower()
    if not chosen:
        raise ValueError("No cloud provider specified and environment variable 'llm_provider' is empty.")

    # map provider -> model name constants
    model_mapping = {
        "mistral": getattr(constants, "mistral_llm", None),
        "gemini": getattr(constants, "gemini_llm", None),
        "openai": getattr(constants, "openai_llm", None),
        "groq": getattr(constants, "groq_llm", None),
    }

    model_name = model_mapping.get(chosen)
    if not model_name:
        raise ValueError(f"Unsupported or unconfigured provider '{chosen}'. Check util.constants and llm_provider env.")

    # map provider -> api keys from env
    api_key_mapping = {
        "mistral": os.getenv("mistral_api_key"),
        "gemini": os.getenv("gemini_api_key"),
        "openai": os.getenv("openai_api_key"),
        "groq": os.getenv("groq_api_key"),
    }
    api_key = api_key_mapping.get(chosen)

    # instantiate appropriate wrapper
    if chosen == "mistral":
        if ChatMistralAI is None:
            raise ValueError("Mistral client wrapper (langchain_mistralai) is not installed.")
        return ChatMistralAI(api_key=api_key, model_name=model_name, temperature=temperature)

    if chosen == "openai":
        if ChatOpenAI is None:
            raise ValueError("OpenAI client wrapper (langchain_openai) is not installed.")
        return ChatOpenAI(api_key=api_key, model=model_name, temperature=temperature)

    if chosen == "gemini":
        if ChatGoogleGenerativeAI is None:
            raise ValueError("Google Generative AI wrapper (langchain_google_genai) is not installed.")
        # Gemini often requires transport selection; use REST by default like earlier code
        return ChatGoogleGenerativeAI(api_key=api_key, model=model_name, temperature=temperature, transport="rest")

    if chosen == "groq":
        if ChatGroq is None:
            raise ValueError("Groq client wrapper (langchain_groq) is not installed.")
        return ChatGroq(api_key=api_key, model=model_name, temperature=temperature)

    # fallback
    raise ValueError(f"Unsupported provider: {chosen}")
