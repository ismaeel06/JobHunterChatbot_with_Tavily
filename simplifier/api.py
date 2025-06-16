from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
import os
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/simplifier", tags=["simplifier"])

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# In-memory cache for explanations
explanation_cache: Dict[str, str] = {}

class SimplificationRequest(BaseModel):
    term: str

class SimplificationResponse(BaseModel):
    term: str
    explanation: str
    cached: bool = False

@router.post("/explain", response_model=SimplificationResponse)
async def explain_term(request: SimplificationRequest):
    """
    Get a simplified explanation of a technical term.
    """
    term = request.term.strip()
    
    if not term:
        raise HTTPException(status_code=400, detail="Term cannot be empty")
    
    # Check cache first
    if term.lower() in explanation_cache:
        logger.info(f"Cache hit for term: {term}")
        return SimplificationResponse(
            term=term,
            explanation=explanation_cache[term.lower()],
            cached=True
        )
    
    # Generate explanation using OpenAI
    try:
        logger.info(f"Generating explanation for: {term}")
        
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant that explains technical terms in extremely 
                    simple, non-technical language. Your target audience is people with no technical 
                    background at all. Use everyday analogies, avoid all jargon, and keep explanations 
                    under 2-3 short sentences. Use the simplest language possible, like explaining to a child."""
                },
                {
                    "role": "user",
                    "content": f"Explain '{term}' in the simplest way possible. No technical terms allowed."
                }
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        explanation = response.choices[0].message.content.strip()
        
        # Cache the explanation
        explanation_cache[term.lower()] = explanation
        
        return SimplificationResponse(
            term=term,
            explanation=explanation,
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate explanation: {str(e)}"
        )

@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get statistics about the explanation cache.
    """
    return {
        "total_cached_terms": len(explanation_cache),
        "cached_terms": list(explanation_cache.keys())
    }

@router.delete("/cache/clear")
async def clear_cache():
    """
    Clear the explanation cache.
    """
    global explanation_cache
    cache_size = len(explanation_cache)
    explanation_cache = {}
    
    return {
        "message": f"Cache cleared. {cache_size} terms removed.",
        "status": "success"
    }