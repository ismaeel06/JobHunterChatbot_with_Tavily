"""
Main application entry point that combines both the Talent Scraper and Term Simplifier.
This provides a cleaner interface and brings together both components.
"""
import logging
import os

# Setup logging first
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Standard imports
from fastapi import FastAPI, HTTPException, Request
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Import modules
from talent_scraper_chatbot import TalentScraperChatbot

# Load environment variables
load_dotenv()

# Create the FastAPI application
app = FastAPI(
    title="AI Talent Tools",
    description="AI-powered talent hunting and technical term simplification",
    version="2.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize the talent scraper chatbot
chatbot = TalentScraperChatbot()

# Import API routers from our modules
from term_simplifier.api import router as simplifier_router
from talent_scraper.api import router as talent_router

# Include the term simplifier API routes
app.include_router(simplifier_router)

# Include the talent scraper API routes
app.include_router(talent_router, prefix="/api/v1", tags=["talent"])

# Root endpoint
@app.get("/")
async def root_endpoint():
    """Root endpoint with API information."""
    return {
        "message": "AI Talent Tools API",
        "description": "API for AI-powered talent hunting and technical term simplification",
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
            "talent_api": "/api/v1",
            "simplifier_api": "/simplifier",
            "simplifier_demo": "/simplifier-demo",
            "health": "/health",
            "docs": "/docs"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check_endpoint():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Talent Tools API",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "tavily_configured": bool(os.getenv("TAVILY_API_KEY"))
    }

# Demo page for the term simplifier
@app.get("/simplifier-demo", include_in_schema=False)
async def simplifier_demo_page(request: Request):
    """Demo page for the technical term simplifier."""
    return templates.TemplateResponse("demo.html", {"request": request})

if __name__ == "__main__":
    print("🚀 Starting AI Talent Tools API...")
    print("🤖 AI-powered talent hunting with OpenAI + Tavily")
    print("🔍 Technical term simplifier enabled")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=log_level.lower()
    )
