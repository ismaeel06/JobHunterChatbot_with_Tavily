from fastapi import FastAPI, HTTPException, APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
import logging
from talent_scraper_chatbot import TalentScraperChatbot, ChatbotResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Talent Scraper Chatbot API",
    description="AI-powered talent scraping chatbot using OpenAI + Tavily",
    version="2.0.0"
)

# Mount static files after initializing the app
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize the chatbot
chatbot = TalentScraperChatbot()

# Create a simplifier router
simplifier_router = APIRouter(prefix="/simplifier", tags=["simplifier"])

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Find me 3 senior React developers with AI experience",
                "session_id": "user123"
            }
        }

class ChatResponse(BaseModel):
    response: str
    search_performed: bool
    talent_count: Optional[int] = None
    search_summary: Optional[str] = None
    conversation_context: Optional[str] = None
    session_id: str

# Simplifier Routes
@simplifier_router.post("/explain")
async def explain_term(request: Request):
    """Get a simplified explanation of a technical term."""
    try:
        # Get the request body
        body = await request.json()
        term = body.get("term", "")

        logger.info(f"Received simplification request for term: '{term}'")
        
        if not term:
            logger.warning("Empty term received in request")
            raise HTTPException(status_code=400, detail="Term is required")
            
        # Use the chatbot's OpenAI client
        from talent_scraper_chatbot import openai_client
        
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
        logger.info(f"Generated explanation for '{term}': {explanation[:30]}...")
        
        return {
            "term": term,
            "explanation": explanation,
            "cached": False
        }
        
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate explanation: {str(e)}"
        )

@simplifier_router.get("/test")
async def test_simplifier():
    """Test endpoint for the simplifier."""
    return {
        "status": "ok",
        "message": "Simplifier API is working"
    }

# Include the simplifier router
app.include_router(simplifier_router)

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Talent Scraper Chatbot API",
        "description": "AI-powered talent scraping using OpenAI + Tavily",
        "version": "2.0.0",
        "capabilities": [
            "Natural language talent search",
            "Multi-platform scraping (Upwork, LinkedIn, GitHub)",
            "AI-powered candidate evaluation",
            "Conversational interface",
            "Risk assessment and ranking",
            "Technical term simplification"
        ],
        "endpoints": {
            "chat": "/api/v1/chat",
            "health": "/health",
            "reset": "/api/v1/reset-conversation", 
            "simplifier": "/simplifier/explain",
            "simplifier_demo": "/simplifier-demo",
            "test_page": "/test-page",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Talent Scraper Chatbot API",
        "chatbot_status": "ready",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "tavily_configured": bool(os.getenv("TAVILY_API_KEY"))
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """
    Chat with the talent scraper bot.
    
    The bot can:
    - Understand natural language talent requests
    - Search for candidates using Tavily
    - Provide detailed candidate analysis
    - Engage in general conversation about talent needs
    """
    try:
        logger.info(f"💬 Chat request from {request.session_id}: {request.message}")
        
        # Process the chat message
        bot_response = await chatbot.chat(request.message)
        
        # Build API response
        response = ChatResponse(
            response=bot_response.message,
            search_performed=bot_response.search_performed,
            talent_count=len(bot_response.talent_results) if bot_response.talent_results else None,
            search_summary=bot_response.search_summary,
            conversation_context=bot_response.conversation_context,
            session_id=request.session_id
        )
        
        logger.info(f"✅ Chat response generated for {request.session_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "session_id": request.session_id
            }
        )

@app.post("/api/v1/reset-conversation")
async def reset_conversation(session_id: str = "default"):
    """Reset conversation history for a session."""
    try:
        chatbot.reset_conversation()
        return {
            "success": True,
            "message": "Conversation history reset successfully",
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/conversation-summary")
async def get_conversation_summary():
    """Get current conversation summary."""
    try:
        summary = chatbot.get_conversation_summary()
        return {
            "success": True,
            "summary": summary,
            "conversation_length": len(chatbot.conversation_history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Test page routes
@app.get("/test-page", include_in_schema=False)
async def test_page(request: Request):
    """Test page for the simplifier API."""
    return templates.TemplateResponse("test.html", {"request": request})

@app.get("/simplifier-demo", include_in_schema=False)
async def simplifier_demo(request: Request):
    """Demo page for the technical term simplifier."""
    return templates.TemplateResponse("demo.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    import os
    
    print("🚀 Starting Talent Scraper Chatbot API...")
    print("🤖 AI-powered talent hunting with OpenAI + Tavily")
    print("💬 Natural language interface available")
    print("🔍 Technical term simplifier enabled")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "chatbot_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )