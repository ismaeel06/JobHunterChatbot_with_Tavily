"""
Tests for the term simplifier API.
To run these tests:
    pytest -xvs tests/test_term_simplifier_api.py
"""
import pytest
from fastapi.testclient import TestClient
from app import app
import os

# Test client for FastAPI
client = TestClient(app)

class TestTermSimplifierAPI:
    """Tests for the term simplifier API."""
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), 
                        reason="OpenAI API key not available")
    def test_explain_endpoint(self):
        """Test the explain endpoint."""
        response = client.post(
            "/simplifier/explain",
            json={
                "term": "API",
                "context": "Web development"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "term" in data
        assert data["term"] == "API"
        assert "explanation" in data
        assert isinstance(data["explanation"], str)
    
    def test_cache_stats(self):
        """Test the cache stats endpoint."""
        response = client.get("/simplifier/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_cached_terms" in data
        assert "cached_terms" in data
        assert isinstance(data["cached_terms"], list)
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        response = client.delete("/simplifier/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
