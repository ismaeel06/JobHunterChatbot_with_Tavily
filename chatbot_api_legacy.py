"""
Modified application entry point for better project structure.

This file serves as a temporary bridge to maintain backward compatibility
while transitioning to the improved project structure.

For new code, please use app.py as the main entry point.
"""
import os
import logging
import asyncio
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the main app
from app import app

if __name__ == "__main__":
    print("⚠️ WARNING: Using chatbot_api.py is deprecated.")
    print("Please use 'python app.py' instead for the main application.")
    print("This file will be removed in a future version.")
    print("")
    
    print("🚀 Starting AI Talent Tools API (legacy entry point)...")
    print("🤖 AI-powered talent hunting with OpenAI + Tavily")
    print("💬 Natural language interface available")
    print("🔍 Technical term simplifier enabled")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
