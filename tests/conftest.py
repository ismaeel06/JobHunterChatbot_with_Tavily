"""
Pytest configuration file with shared fixtures.
"""
import pytest
import os
from dotenv import load_dotenv

# Load environment variables for tests
@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables before running tests."""
    load_dotenv()
    
    # Verify required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Warning: OPENAI_API_KEY not set. Some tests will be skipped.")
    
    if not os.getenv("TAVILY_API_KEY"):
        print("⚠️ Warning: TAVILY_API_KEY not set. Some tests will be skipped.")
