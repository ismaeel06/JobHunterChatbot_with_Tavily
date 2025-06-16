import os
import logging
from typing import Dict, Optional, List
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

class SimplifierService:
    """Service for simplifying technical terms using OpenAI."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found in environment variables")
            
        self.openai_client = AsyncOpenAI(api_key=self.api_key)
        self.cache: Dict[str, str] = {}
        self.technical_terms: List[str] = self._load_common_technical_terms()
    
    async def simplify_term(self, term: str) -> str:
        """Generate a simple explanation for a technical term."""
        term = term.strip().lower()
        
        # Check cache first
        if term in self.cache:
            logger.info(f"Using cached explanation for: {term}")
            return self.cache[term]
        
        try:
            logger.info(f"Generating explanation for: {term}")
            
            response = await self.openai_client.chat.completions.create(
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
            self.cache[term] = explanation
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error simplifying term '{term}': {str(e)}")
            return f"Sorry, I couldn't explain that term right now."
    
    def is_technical_term(self, term: str) -> bool:
        """Check if a word is likely to be a technical term."""
        term = term.strip().lower()
        
        if term in self.technical_terms:
            return True
        
        # Simple heuristic: technical terms are often longer than 4 characters
        # and don't appear in common English words
        if len(term) <= 4:
            return False
            
        # Add more sophisticated detection as needed
        return True
    
    def clear_cache(self) -> int:
        """Clear the explanation cache and return number of items cleared."""
        cache_size = len(self.cache)
        self.cache = {}
        return cache_size
    
    def _load_common_technical_terms(self) -> List[str]:
        """Load a list of common technical terms."""
        # This would ideally come from a file, but for simplicity we'll hardcode some
        return [
            "api", "rest", "json", "http", "url", "html", "css", "javascript",
            "python", "database", "sql", "server", "client", "backend", "frontend",
            "framework", "library", "function", "variable", "algorithm", "data structure",
            "cloud", "hosting", "deployment", "container", "docker", "kubernetes",
            "microservice", "authentication", "authorization", "encryption", "api key",
            "endpoint", "request", "response", "status code", "header", "payload",
            "git", "repository", "commit", "branch", "merge", "pull request",
            "compiler", "interpreter", "runtime", "debugging", "testing", "unit test",
            "integration test", "continuous integration", "continuous deployment",
            "agile", "scrum", "waterfall", "sprint", "backlog", "user story",
            "bandwidth", "latency", "throughput", "cache", "memory", "cpu", "gpu",
            "thread", "process", "asynchronous", "synchronous", "concurrency",
            "ajax", "xml", "yaml", "markdown", "regex", "expression", "statement"
        ]