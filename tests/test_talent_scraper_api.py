"""
Tests for the talent scraper API.
To run these tests:
    pytest -xvs tests/test_talent_scraper_api.py
"""
import pytest
from fastapi.testclient import TestClient
from app import app
import os

# Test client for FastAPI
client = TestClient(app)

class TestTalentScraperAPI:
    """Tests for the talent scraper API."""
    
    def setup_method(self):
        """Setup for tests."""
        self.session_id = "test_session_123"
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"), 
                        reason="API keys not available")
    def test_chat_endpoint(self):
        """Test the chat endpoint."""
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Hello, what can you help me with?",
                "session_id": self.session_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
        assert "session_id" in data
        assert data["session_id"] == self.session_id
    
    def test_reset_conversation(self):
        """Test the reset conversation endpoint."""
        response = client.post(f"/api/v1/reset-conversation?session_id={self.session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_conversation_summary(self):
        """Test the conversation summary endpoint."""
        response = client.get("/api/v1/conversation-summary")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
