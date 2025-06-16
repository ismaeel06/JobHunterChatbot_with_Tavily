"""
Models module for the Talent Scraper.
Contains data classes and types used throughout the application.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional

class SeniorityLevel(str, Enum):
    """Enum for talent seniority levels."""
    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"
    PRINCIPAL = "Principal"

@dataclass
class Talent:
    """Represents a talent profile."""
    title: str
    purpose: str
    seniority: SeniorityLevel
    skill_keywords: List[str]
    profile_url: Optional[str] = None
    experience_years: Optional[str] = None
    rating: Optional[str] = None
    hourly_rate: Optional[str] = None
    risk_score: Optional[int] = None
    strengths: Optional[List[str]] = None
    summary: Optional[str] = None

@dataclass
class ChatbotResponse:
    """Response from the talent scraper chatbot."""
    message: str
    talent_results: Optional[List[Talent]] = None
    search_performed: bool = False
    search_summary: Optional[str] = None
    conversation_context: Optional[str] = None
