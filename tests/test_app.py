"""
Tests for the main application entry points.
To run these tests:
    pytest -xvs tests/test_app.py
"""
import pytest
from fastapi.testclient import TestClient
from app import app

# Test client for FastAPI
client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "AI Talent Tools API"
    assert "endpoints" in data

def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_simplifier_demo_page():
    """Test the simplifier demo page."""
    response = client.get("/simplifier-demo")
    assert response.status_code == 200
    assert "html" in response.text.lower()
    assert "Technical Term Simplifier Demo" in response.text
