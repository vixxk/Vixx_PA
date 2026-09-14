from langchain_groq import ChatGroq
from app.config import settings
from fastapi import HTTPException, status
import logging
from typing import List, Optional
from langchain_core.messages import BaseMessage, AIMessage

logger = logging.getLogger(__name__)

FALLBACK_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound-mini",
]

def get_llm(model_name: Optional[str] = None):
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set. AI functions will fail until key is provided.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GROQ_API_KEY is not configured. Please add it to your .env file."
        )
    
    target_model = model_name or settings.GROQ_MODEL or "qwen/qwen3.8-27b"
    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=target_model,
        temperature=0.0
    )


async def invoke_llm_with_fallback(messages: List[BaseMessage], temperature: float = 0.0) -> AIMessage:
    """
    Invokes Groq LLM with automatic fallback through verified available models
    if the primary model encounters a 404, rate limit, or not-found error.
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GROQ_API_KEY is not configured. Please add it to your .env file."
        )

    primary_model = settings.GROQ_MODEL or "qwen/qwen3.8-27b"
    models_to_try = [primary_model] + [m for m in FALLBACK_MODELS if m != primary_model]
    
    last_error = None
    for model in models_to_try:
        try:
            llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=model,
                temperature=temperature
            )
            response = await llm.ainvoke(messages)
            return response
        except Exception as err:
            err_str = str(err).lower()
            logger.warning(f"Groq model '{model}' failed: {err_str}. Trying fallback...")
            last_error = err
            if "invalid api key" in err_str or "unauthorized" in err_str or "401" in err_str:
                raise err
            continue

    logger.error(f"All Groq models failed. Last error: {last_error}")
    raise last_error
