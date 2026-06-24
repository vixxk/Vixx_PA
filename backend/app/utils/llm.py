from langchain_groq import ChatGroq
from app.config import settings
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

def get_llm():
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set. AI functions will fail until key is provided.")
        # Return a dummy or raise error when invoked.
        # We will raise a clean HTTP exception if the user tries to run it.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GROQ_API_KEY is not configured. Please add it to your .env file."
        )
    
    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=settings.GROQ_MODEL,
        temperature=0.0
    )
