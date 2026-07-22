import logging
from dataclasses import dataclass

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# Model configuration
_MODEL = "gpt-4o-mini"
_TEMPERATURE = 0.1
_MAX_TOKENS = 4096

# Lazy-initialized client (shared with embeddings but separate instance
# to keep module boundaries clean)
_client: OpenAI | None = None


@dataclass
class LLMResult:
    """Result from an LLM completion call."""

    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str


def _get_client() -> OpenAI:
    """Get or create the OpenAI client."""
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. "
                "Set it in your .env file to use the chat feature."
            )
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI client initialized for chat completions")
    return _client


def generate_response(
    messages: list[dict[str, str]],
    model: str = _MODEL,
    temperature: float = _TEMPERATURE,
    max_tokens: int = _MAX_TOKENS,
) -> LLMResult:
    client = _get_client()

    try:
        logger.info(
            "Calling OpenAI %s (messages=%d, temp=%.1f, max_tokens=%d)",
            model,
            len(messages),
            temperature,
            max_tokens,
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = response.usage

        result = LLMResult(
            content=choice.message.content or "",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            model=response.model,
        )

        logger.info(
            "OpenAI response: %d chars, %d prompt tokens, %d completion tokens",
            len(result.content),
            result.prompt_tokens,
            result.completion_tokens,
        )

        return result

    except Exception as e:
        logger.error("OpenAI API call failed: %s", e)
        raise RuntimeError(f"LLM call failed: {e}") from e
