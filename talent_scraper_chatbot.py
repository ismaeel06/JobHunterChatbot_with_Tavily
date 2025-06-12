import os
import json
import asyncio
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from tavily import TavilyClient
import logging
import openai
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Data Models
class SeniorityLevel(str, Enum):
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

class TalentScraperChatbot:
    """AI-powered talent scraper chatbot using OpenAI + Tavily."""
    
    def __init__(self):
        self.name = "Talent Scraper Assistant"
        self.description = "AI chatbot that finds and evaluates talent using Tavily web scraping"
        self.conversation_history = []
        self.system_prompt = self._build_system_prompt()
        self.search_platforms = [
            "site:upwork.com/freelancers",
            "site:linkedin.com/in",
            "site:github.com",
            "site:stackoverflow.com/users",
            "site:freelancer.com"
        ]
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the OpenAI model."""
        return """
You are a Talent Scraper Assistant - an expert AI agent specialized in finding and evaluating talent.

Your capabilities:
- Understand talent requirements from natural language
- Use Tavily web scraping to find candidates
- Evaluate and rank talent based on skills, experience, and risk
- Provide detailed insights about candidates

Your tools:
- Tavily: For searching talent across platforms (Upwork, LinkedIn, GitHub, etc.)

When a user asks for talent:
1. Acknowledge their request professionally
2. Extract key requirements (skills, seniority, quantity, etc.)
3. Use Tavily to search for matching talent
4. Analyze and present the best candidates
5. Provide recommendations and insights

Always be helpful, professional, and thorough in your responses.
Focus on understanding the user's specific needs and delivering high-quality talent matches.

If the user asks general questions or wants to chat, respond naturally but always guide the conversation toward talent-related topics when appropriate.
"""

    async def chat(self, user_message: str) -> ChatbotResponse:
        """Main chat interface - processes user message and returns response."""
        
        try:
            logger.info(f"💬 User message: {user_message}")
            
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user", 
                "content": user_message
            })
            
            # Determine if this is a talent search request
            search_intent = await self._analyze_search_intent(user_message)
            
            if search_intent["is_talent_request"]:
                # Perform talent search
                return await self._handle_talent_search(user_message, search_intent)
            else:
                # Handle general conversation
                return await self._handle_general_chat(user_message)
                
        except Exception as e:
            logger.error(f"❌ Chat error: {str(e)}")
            return ChatbotResponse(
                message=f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                search_performed=False
            )

    async def _analyze_search_intent(self, message: str) -> Dict[str, Any]:
        """Analyze if the user message is requesting talent search."""
        
        intent_prompt = f"""
Analyze this message to determine if the user is requesting talent/developer search:

Message: "{message}"

Return JSON with:
{{
    "is_talent_request": true/false,
    "skills": ["list of technical skills mentioned"],
    "seniority": "junior/mid/senior/lead/principal or null",
    "quantity": number or null,
    "platform_preference": "upwork/linkedin/github/any or null",
    "urgency": "high/medium/low",
    "additional_requirements": "any other specific requirements"
}}

Examples of talent requests:
- "Find me 3 React developers"
- "I need senior Python engineers with ML experience"
- "Search for MERN stack freelancers"
- "Can you help me find DevOps experts?"
"""

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing user intent for talent search. Always respond with valid JSON."},
                    {"role": "user", "content": intent_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            intent_data = json.loads(response.choices[0].message.content)
            logger.info(f"🧠 Search intent analyzed: {intent_data}")
            return intent_data
            
        except Exception as e:
            logger.error(f"❌ Intent analysis error: {str(e)}")
            # Fallback: simple keyword detection
            talent_keywords = ["find", "search", "need", "developer", "engineer", "programmer", "talent", "hire", "recruit"]
            is_talent_request = any(keyword in message.lower() for keyword in talent_keywords)
            
            return {
                "is_talent_request": is_talent_request,
                "skills": [],
                "seniority": None,
                "quantity": None,
                "platform_preference": None,
                "urgency": "medium",
                "additional_requirements": ""
            }

    async def _handle_talent_search(self, user_message: str, search_intent: Dict[str, Any]) -> ChatbotResponse:
        """Handle talent search requests."""
        
        # Generate search acknowledgment
        search_ack = await self._generate_search_acknowledgment(user_message, search_intent)
        
        # Perform the actual talent search using Tavily
        talent_results = await self._search_talent_with_tavily(user_message, search_intent)
        
        # Generate final response with results
        final_response = await self._generate_results_response(talent_results, search_intent)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })
        
        return ChatbotResponse(
            message=final_response,
            talent_results=talent_results,
            search_performed=True,
            search_summary=f"Found {len(talent_results)} candidates matching your criteria",
            conversation_context="talent_search_completed"
        )

    async def _handle_general_chat(self, user_message: str) -> ChatbotResponse:
        """Handle general conversation."""
        
        # Prepare conversation for OpenAI
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history[-10:]  # Keep last 10 messages for context
        
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            ai_response = response.choices[0].message.content
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            return ChatbotResponse(
                message=ai_response,
                search_performed=False,
                conversation_context="general_chat"
            )
            
        except Exception as e:
            logger.error(f"❌ General chat error: {str(e)}")
            return ChatbotResponse(
                message="I'm here to help you find talent! What kind of developers or professionals are you looking for?",
                search_performed=False
            )

    async def _generate_search_acknowledgment(self, user_message: str, search_intent: Dict[str, Any]) -> str:
        """Generate acknowledgment message for search request."""
        
        skills = search_intent.get("skills", [])
        seniority = search_intent.get("seniority", "")
        quantity = search_intent.get("quantity", "")
        
        ack_parts = ["🔍 I'll help you find"]
        
        if quantity:
            ack_parts.append(f"{quantity}")
        
        if seniority:
            ack_parts.append(f"{seniority}")
        
        if skills:
            if len(skills) > 1:
                ack_parts.append(f"{', '.join(skills[:-1])} and {skills[-1]}")
            else:
                ack_parts.append(skills[0])
        
        ack_parts.append("developers. Let me search across multiple platforms...")
        
        return " ".join(ack_parts)

    async def _search_talent_with_tavily(self, user_message: str, search_intent: Dict[str, Any]) -> List[Talent]:
        """Perform actual talent search using Tavily - integrated talent hunting logic."""
        
        try:
            logger.info(f"🎯 Starting talent hunt for: {user_message}")
            
            # Step 1: Decompose requirements
            requirements = await self._decompose_requirements(user_message)
            
            # Step 2: Generate search queries
            search_queries = self._generate_search_queries(requirements)
            
            # Step 3: Execute searches
            search_results = await self._execute_searches(search_queries)
            
            # Step 4: Extract and evaluate talent
            talent_profiles = await self._extract_talent_profiles(search_results)
            
            # Step 5: Rank and filter
            final_talent_list = self._rank_and_filter_talent(talent_profiles, requirements)
            
            return final_talent_list
            
        except Exception as e:
            logger.error(f"❌ Talent search error: {str(e)}")
            return [self._create_error_talent(str(e))]

    async def _decompose_requirements(self, user_input: str) -> Dict[str, Any]:
        """Decompose user input into structured requirements."""
        
        user_lower = user_input.lower()
        
        # Extract technologies/skills
        tech_keywords = {
            "react": ["React", "ReactJS", "Frontend"],
            "node": ["Node.js", "NodeJS", "Backend"],
            "python": ["Python", "Django", "Flask"],
            "javascript": ["JavaScript", "JS", "Frontend"],
            "mongodb": ["MongoDB", "NoSQL", "Database"],
            "express": ["Express.js", "ExpressJS"],
            "ai": ["AI", "Machine Learning", "Deep Learning"],
            "fullstack": ["Full Stack", "Full-Stack", "Fullstack"],
            "mern": ["MERN", "MongoDB", "Express", "React", "Node"],
            "devops": ["DevOps", "AWS", "Docker", "Kubernetes"],
            "mobile": ["React Native", "Flutter", "iOS", "Android"]
        }
        
        # Extract seniority level
        seniority_map = {
            "junior": SeniorityLevel.JUNIOR,
            "mid": SeniorityLevel.MID,
            "senior": SeniorityLevel.SENIOR,
            "lead": SeniorityLevel.LEAD,
            "principal": SeniorityLevel.PRINCIPAL,
            "entry": SeniorityLevel.JUNIOR,
            "experienced": SeniorityLevel.SENIOR,
            "expert": SeniorityLevel.SENIOR
        }
        
        extracted_skills = []
        for key, skills in tech_keywords.items():
            if key in user_lower:
                extracted_skills.extend(skills)
        
        extracted_seniority = SeniorityLevel.MID  # Default
        for key, level in seniority_map.items():
            if key in user_lower:
                extracted_seniority = level
                break
        
        # Extract quantity
        quantity_match = re.search(r'(\d+)', user_input)
        quantity = int(quantity_match.group(1)) if quantity_match else 5
        
        requirements = {
            "skills": list(set(extracted_skills)) if extracted_skills else ["Software Development"],
            "seniority": extracted_seniority,
            "quantity": min(quantity, 10),  # Limit to 10
            "original_request": user_input
        }
        
        logger.info(f"📋 Extracted requirements: {requirements}")
        return requirements

    def _generate_search_queries(self, requirements: Dict[str, Any]) -> List[str]:
        """Generate optimized search queries based on requirements."""
        
        skills = requirements.get("skills", [])
        seniority = requirements.get("seniority", SeniorityLevel.MID)
        
        # Create skill combinations
        skill_string = " ".join(skills[:4])  # Limit to avoid too long queries
        
        queries = []
        
        # Platform-specific queries
        for platform in self.search_platforms[:3]:  # Use top 3 platforms
            if "upwork" in platform:
                query = f"{skill_string} {seniority.value} developer {platform}"
            elif "linkedin" in platform:
                query = f"{skill_string} software engineer {seniority.value} {platform}"
            else:
                query = f"{skill_string} developer {platform}"
            
            queries.append(query)
        
        # Add general queries
        queries.extend([
            f"{skill_string} {seniority.value} developer freelancer",
            f"{skill_string} software engineer remote",
            f"{skill_string} consultant expert developer"
        ])
        
        logger.info(f"🔍 Generated {len(queries)} search queries")
        return queries[:5]  # Limit to 5 queries to avoid rate limits

    async def _execute_searches(self, search_queries: List[str]) -> List[Dict[str, Any]]:
        """Execute searches using Tavily."""
        
        all_results = []
        
        for i, query in enumerate(search_queries, 1):
            try:
                logger.info(f"🌐 Executing search {i}/{len(search_queries)}: {query}")
                
                response = tavily_client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5,
                    include_answer=True,
                    include_raw_content=True
                )
                
                results = response.get('results', [])
                logger.info(f"📊 Found {len(results)} results for query {i}")
                
                # Add query context to each result
                for result in results:
                    result['search_query'] = query
                    result['search_index'] = i
                
                all_results.extend(results)
                
                # Add delay to respect rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Search error for query '{query}': {str(e)}")
                continue
        
        logger.info(f"✅ Total search results collected: {len(all_results)}")
        return all_results

    async def _extract_talent_profiles(self, search_results: List[Dict[str, Any]]) -> List[Talent]:
        """Extract structured talent profiles from search results."""
        
        talent_profiles = []
        
        for i, result in enumerate(search_results, 1):
            try:
                logger.info(f"🔍 Extracting profile {i}/{len(search_results)}")
                
                title = result.get('title', 'Unknown Developer')
                url = result.get('url', '')
                content = result.get('content', '')
                
                # Extract information using pattern matching
                profile_data = self._extract_profile_data(title, content, url)
                
                # Create talent object
                talent = Talent(
                    title=profile_data.get('name', f"Developer {i}"),
                    purpose=profile_data.get('role_description', "Software development professional"),
                    seniority=profile_data.get('seniority', SeniorityLevel.MID),
                    skill_keywords=profile_data.get('skills', []),
                    profile_url=url,
                    experience_years=profile_data.get('experience', 'Not specified'),
                    rating=profile_data.get('rating', 'Not specified'),
                    hourly_rate=profile_data.get('rate', 'Not specified'),
                    risk_score=profile_data.get('risk_score', 3),
                    strengths=profile_data.get('strengths', []),
                    summary=content[:200] + "..." if len(content) > 200 else content
                )
                
                talent_profiles.append(talent)
                
            except Exception as e:
                logger.error(f"❌ Error extracting profile {i}: {str(e)}")
                continue
        
        logger.info(f"✅ Extracted {len(talent_profiles)} talent profiles")
        return talent_profiles

    def _extract_profile_data(self, title: str, content: str, url: str) -> Dict[str, Any]:
        """Extract structured data from profile text."""
        
        profile_data = {
            'name': 'Unknown',
            'skills': [],
            'experience': 'Not specified',
            'rating': 'Not specified',
            'rate': 'Not specified',
            'seniority': SeniorityLevel.MID,
            'strengths': [],
            'risk_score': 3,
            'role_description': 'Software development professional'
        }
        
        # Extract name (first part of title)
        name_match = re.search(r'^([A-Za-z\s]+?)(?:\s*[-–|]|\s*\d|\s*$)', title)
        if name_match:
            profile_data['name'] = name_match.group(1).strip()
        
        # Extract skills
        skill_patterns = [
            'React', 'Node.js', 'Python', 'JavaScript', 'MongoDB', 'Express',
            'AI', 'Machine Learning', 'DevOps', 'AWS', 'Docker', 'TypeScript',
            'Full Stack', 'Frontend', 'Backend', 'Mobile', 'Flutter'
        ]
        
        found_skills = []
        text_to_search = (title + " " + content).lower()
        
        for skill in skill_patterns:
            if skill.lower() in text_to_search:
                found_skills.append(skill)
        
        profile_data['skills'] = found_skills
        
        # Extract experience
        exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)', content.lower())
        if exp_match:
            years = int(exp_match.group(1))
            profile_data['experience'] = f"{years} years"
            
            # Determine seniority based on experience
            if years < 2:
                profile_data['seniority'] = SeniorityLevel.JUNIOR
            elif years < 5:
                profile_data['seniority'] = SeniorityLevel.MID
            elif years < 8:
                profile_data['seniority'] = SeniorityLevel.SENIOR
            else:
                profile_data['seniority'] = SeniorityLevel.LEAD
        
        # Extract rating
        rating_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:stars?|rating|\/5)', content.lower())
        if rating_match:
            profile_data['rating'] = f"{rating_match.group(1)}/5"
        
        # Extract hourly rate
        rate_match = re.search(r'\$(\d+)(?:\.\d+)?\/(?:hour|hr)', content.lower())
        if rate_match:
            profile_data['rate'] = f"${rate_match.group(1)}/hour"
        
        # Calculate risk score (1-5, lower is better)
        risk_score = 3  # Default medium risk
        
        if len(found_skills) >= 5:
            risk_score -= 1  # Strong skill set
        if 'upwork.com' in url or 'linkedin.com' in url:
            risk_score -= 0.5  # Verified platform
        if profile_data['rating'] != 'Not specified':
            risk_score -= 0.5  # Has ratings
        if 'Not specified' in profile_data['experience']:
            risk_score += 1  # Missing experience info
        
        profile_data['risk_score'] = max(1, min(5, int(risk_score)))
        
        # Determine strengths
        strengths = []
        if len(found_skills) >= 5:
            strengths.append("Diverse skill set")
        if 'Full Stack' in found_skills or ('Frontend' in found_skills and 'Backend' in found_skills):
            strengths.append("Full-stack capabilities")
        if any(ai in found_skills for ai in ['AI', 'Machine Learning']):
            strengths.append("AI/ML expertise")
        if 'upwork.com' in url:
            strengths.append("Upwork verified")
        
        profile_data['strengths'] = strengths
        
        return profile_data

    def _rank_and_filter_talent(self, talent_profiles: List[Talent], requirements: Dict[str, Any]) -> List[Talent]:
        """Rank and filter talent based on requirements."""
        
        required_skills = set(skill.lower() for skill in requirements.get('skills', []))
        target_quantity = requirements.get('quantity', 5)
        
        # Calculate match scores
        for talent in talent_profiles:
            talent_skills = set(skill.lower() for skill in talent.skill_keywords)
            skill_match = len(required_skills.intersection(talent_skills))
            total_skills = len(talent.skill_keywords)
            
            # Calculate overall score (lower is better)
            match_score = (
                (talent.risk_score or 3) * 0.4 +  # Risk weight
                max(0, 5 - skill_match) * 0.4 +    # Skill match weight  
                max(0, 5 - total_skills/2) * 0.2    # Total skills weight
            )
            
            talent.match_score = match_score
        
        # Sort by match score (lower is better)
        sorted_talent = sorted(talent_profiles, key=lambda x: getattr(x, 'match_score', 5))
        
        # Return top candidates
        top_talent = sorted_talent[:target_quantity]
        
        logger.info(f"🏆 Selected top {len(top_talent)} candidates")
        return top_talent

    def _create_error_talent(self, error_message: str) -> Talent:
        """Create an error talent object."""
        return Talent(
            title="System Error",
            purpose=f"Error occurred during talent search: {error_message}",
            seniority=SeniorityLevel.SENIOR,
            skill_keywords=["troubleshooting", "system administration"],
            summary="An error occurred during the talent hunting process."
        )

    async def _generate_results_response(self, talent_results: List[Talent], search_intent: Dict[str, Any]) -> str:
        """Generate a comprehensive response with talent search results."""
        
        if not talent_results:
            return "🚫 I couldn't find any candidates matching your exact criteria. Would you like me to try a broader search or adjust the requirements?"
        
        # Prepare results for OpenAI to format
        results_data = []
        for talent in talent_results:
            results_data.append({
                "name": talent.title,
                "skills": talent.skill_keywords,
                "experience": talent.experience_years,
                "rating": talent.rating,
                "rate": talent.hourly_rate,
                "risk_score": talent.risk_score,
                "strengths": talent.strengths,
                "summary": talent.summary
            })
        
        format_prompt = f"""
Format these talent search results into a professional, engaging response:

Search Results: {json.dumps(results_data, indent=2)}

Requirements:
- Start with a success message about finding {len(talent_results)} candidates
- Present each candidate clearly with key highlights
- Include risk assessment and recommendations
- End with an offer to help further or refine the search
- Use emojis appropriately for visual appeal
- Be conversational but professional

Make it informative and easy to read.
"""

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional talent acquisition specialist. Format search results in an engaging, informative way."},
                    {"role": "user", "content": format_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ Response formatting error: {str(e)}")
            # Fallback to simple formatting
            response_parts = [f"✅ Great! I found {len(talent_results)} talented candidates for you:\n"]
            
            for i, talent in enumerate(talent_results[:5], 1):
                response_parts.append(f"\n{i}. **{talent.title}**")
                response_parts.append(f"   💼 Skills: {', '.join(talent.skill_keywords[:5])}")
                response_parts.append(f"   ⭐ Experience: {talent.experience_years}")
                response_parts.append(f"   📊 Risk Score: {talent.risk_score}/5")
                if talent.profile_url:
                    response_parts.append(f"   🔗 Profile: {talent.profile_url}")
            
            response_parts.append("\n\nWould you like me to provide more details about any of these candidates or search for additional talent?")
            
            return "\n".join(response_parts)

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        logger.info("🔄 Conversation history reset")

    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation."""
        if not self.conversation_history:
            return "No conversation history yet."
        
        messages_count = len(self.conversation_history)
        user_messages = len([msg for msg in self.conversation_history if msg["role"] == "user"])
        
        return f"Conversation: {messages_count} total messages, {user_messages} from user"

# Export for use
__all__ = ['TalentScraperChatbot', 'ChatbotResponse', 'Talent', 'SeniorityLevel']