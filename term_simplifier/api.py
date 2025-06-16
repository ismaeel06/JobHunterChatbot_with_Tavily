"""
API module for the Term Simplifier.
Contains FastAPI routes for the technical term simplification service.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Optional
import os
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI
from .service import SimplifierService

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/simplifier", tags=["simplifier"])

# Initialize simplifier service
simplifier_service = SimplifierService()

# In-memory cache for explanations
explanation_cache: Dict[str, str] = {}

class SimplificationRequest(BaseModel):
    term: str
    context: Optional[str] = None

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
    
    # Generate explanation using the service
    try:
        explanation = await simplifier_service.simplify_term(term, request.context)
        
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
