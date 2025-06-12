from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
import logging
from talent_scraper_chatbot import TalentScraperChatbot, ChatbotResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Talent Scraper Chatbot API",
    description="AI-powered talent scraping chatbot using OpenAI + Tavily",
    version="2.0.0"
)

# Initialize the chatbot
chatbot = TalentScraperChatbot()

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
            "Risk assessment and ranking"
        ],
        "endpoints": {
            "chat": "/api/v1/chat",
            "health": "/health",
            "reset": "/api/v1/reset-conversation",
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

if __name__ == "__main__":
    import uvicorn
    import os
    
    print("🚀 Starting Talent Scraper Chatbot API...")
    print("🤖 AI-powered talent hunting with OpenAI + Tavily")
    print("💬 Natural language interface available")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "chatbot_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )