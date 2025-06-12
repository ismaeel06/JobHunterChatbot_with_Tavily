import os
import json
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from tavily import TavilyClient
import re

# Load environment variables from .env file
load_dotenv()

# Initialize Tavily client with API key
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Define the comprehensive state for our multi-agent system
class DeveloperSearchState(TypedDict):
    # Input
    user_request: str  # User's original search request

    # Search Refinement Agent:
    refined_search_query: str  # Refined search query after processing
    search_keywords: List[str]  # Keywords extracted from the refined query

    # Tavily Search
    raw_search_results: Dict[str, Any]  # Raw results from Tavily API

    # Risk Assessment Agent:
    evaluated_developers: List[Dict[str, Any]]  # Developers evaluated for risk

    #Final Output
    final_recommendations: List[Dict[str, Any]]  # Final recommendations for the user

    # System
    messages: Annotated[List, "Conversation history"]
    current_step: str  # Current step in the process


# ==================== AGENT 1: SEARCH REFINEMENT AGENT ====================

def search_refinement_agent(state: DeveloperSearchState) -> DeveloperSearchState:
    """
    This agent refines the user's search query and extracts keywords.
    """
    print("Running Search Refinement Agent...")
    print("=" * 50)

    user_request = state.get("user_request", "")
    print(f"Processing Request: {user_request}")

    #Extract key technologies and skills
    mern_keywords = ["MongoDB", "Express.js", "React", "Node.js"]
    ai_keywords = ["Machine Learning", "AI", "Artificial Intelligence", "Deep Learning", "TensorFlow", "PyTorch"]
    quality_indicators = ["top rated", "expert level", "5 stars", "certified", "experienced"]

    #Create comprehensive search queries
    search_queries = [
        "MERN stack developer MongoDB Express React Node.js AI machine learning site:upwork.com/freelancers",
        "full stack developer React Node.js MongoDB artificial intelligence top rated site:upwork.com",
        "JavaScript developer React Express MongoDB AI deep learning expert site:upwork.com/freelancers",
        "MERN developer artificial intelligence machine learning certified site:upwork.com",
        "full stack JavaScript MongoDB React Node Express AI developer site:upwork.com/freelancers"
    ]
     
    # Select the most comprehensive query
    refined_query = search_queries[0]
    
    #Extract all relevant kewords
    all_keywords = mern_keywords + ai_keywords + quality_indicators

    state["refined_search_query"] = refined_query
    state["search_keywords"] = all_keywords
    state["current_step"] = "search_refinement_complete"

    print(f"🎯 Refined Search Query: {refined_query}")
    print(f"🏷️  Keywords Extracted: {', '.join(all_keywords[:8])}...")
    print("✅ Search refinement complete!")
    
    # Add to conversation history
    state["messages"].append(
        AIMessage(content=f"Search query refined: {refined_query}")
    )
    
    return state

# ==================== AGENT 2: TAVILY SEARCH AGENT ====================

def tavily_search_agent(state: DeveloperSearchState) -> DeveloperSearchState:
    """
    This agent performs the actual web search using Tavily.
    """
    print("Running Tavily Search Agent...")
    print("=" * 50)

    search_query = state.get("refined_search_query", "")
    print(f"Performing search for: {search_query}")

    try:
        #Execute search using Tavily
        response = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            max_results=10,  # Limit to 10 results for better performance
            include_answer=True,  # Include direct answers if available
            include_raw_content=True
        )

        state["raw_search_results"] = response
        state["current_step"] = "tavily_search_complete"

        results_count = len(response.get('results', []))
        print(f"🌐 Found {results_count} results for query: {search_query}")

        # Preview first few results
        for i, result in enumerate(response.get('results', [])[:3], 1):
            title = result.get('title', 'No Title')[:60]
            url = result.get('url', 'No URL')
            content = result.get('content', 'No content')[:200] + "..."
            print(f"{i}. **{title}**\n   URL: {url}\n   Content: {content}\n")

        print("✅ Tavily search complete!")
        
        # Add to conversation history
        state["messages"].append(
            AIMessage(content=f"Found {results_count} developer profiles from web search")
        )
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        state["raw_search_results"] = {"results": [], "error": str(e)}
        state["current_step"] = "tavily_search_error"
    
    return state

# ==================== AGENT 3: RISK ASSESSMENT AGENT ====================

def risk_assessment_agent(state: DeveloperSearchState) -> DeveloperSearchState:
    """
    This agent evaluates the developers found in the search results for risk.
    """
    print("Running Risk Assessment Agent...")
    print("=" * 50)

    raw_results = state.get("raw_search_results", {})
    search_results = raw_results.get('results', [])

    if not search_results:
        print("❌ No search results to evaluate.")
        state["evaluated_developers"] = []
        state["current_step"] = "risk_assessment_complete"
        return state
    
    print(f"📋 Analyzing {len(search_results)} developer profiles...")
    
    evaluated_developers = []

    for i, result in enumerate(search_results[:5], 1):
        print(f"Evaluating profile {i}:")

        #Extract basic information
        title = result.get('title', 'Unknown Developer')
        url = result.get('url', 'No URL')
        content = result.get('content', 'No content available')

        #Extract developer information using pattern matching
        developer_profile = extract_developer_info(title, content, url)

        #Calculate Risk Score 
        risk_score = calculate_risk_score(developer_profile, content)

        #Create structured profile
        structured_profile = {
            "id": i,
            "name": developer_profile.get("name", f"Developer {i}"),
            "profile_url": url,
            "title": title,
            "skills": developer_profile.get("skills", []),
            "experience_years": developer_profile.get("experience", "Unknown"),
            "rating": developer_profile.get("rating", "Not specified"),
            "hourly_rate": developer_profile.get("rate", "Not specified"),
            "risk_score": risk_score,
            "risk_level": get_risk_level(risk_score),
            "risk_factors": developer_profile.get("risk_factors", []),
            "strengths": developer_profile.get("strengths", []),
            "summary": content[:200] + "..." if len(content) > 200 else content
        }

        evaluated_developers.append(structured_profile)
        print(f"   👤 Name: {structured_profile['name']}")
        print(f"   ⭐ Risk Score: {risk_score}/5 ({structured_profile['risk_level']})")
        print(f"   🔗 Profile: {url[:50]}...")
    
    state["evaluated_developers"] = evaluated_developers
    state["current_step"] = "risk_assessment_complete"

    print(f"\n✅ Risk assessment complete! Evaluated {len(evaluated_developers)} developers")
    
    # Add to conversation history
    state["messages"].append(
        AIMessage(content=f"Completed risk assessment for {len(evaluated_developers)} developers")
    )

    return state
# ==================== HELPER FUNCTIONS ====================

def extract_developer_info(title: str, content: str, url: str) -> Dict[str, Any]:
    """
    Extracts relevant information from a developer's profile.
    """
    profile = {
       "name": "Unknown",
       "skills": [],
       "experience": "Unknown",
       "rating": "Not specified",
       "rate": "Not specified",
       "risk_factors": [],
       "strengths": []
   }
    
    # Extract name (if available)
    name_match = re.search(r'^([A-Za-z\s]+?)(?:\s*[-–|]|\s*\d|\s*$)', title)
    if name_match:
        profile["name"] = name_match.group(1).strip()

    # Extract Skills
    mern_skills = ["MongoDB", "Express", "React", "Node", "JavaScript", "Full Stack"]
    ai_skills = ["AI", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "NLP"]

    found_skills = []
    text_to_search = (title + " " + content).lower()

    for skill in mern_skills + ai_skills:
        if skill.lower() in text_to_search:
            found_skills.append(skill)
    profile["skills"] = found_skills

    # Extract Experience
    exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)', content.lower())
    if exp_match:
        profile["experience"] = f"{exp_match.group(1)} years"

    # Extract rating
    rating_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:stars?|rating|\/5)', content.lower())
    if rating_match:
        profile["rating"] = f"{rating_match.group(1)}/5"
    
    # Extract hourly rate
    rate_match = re.search(r'\$(\d+)(?:\.\d+)?\/(?:hour|hr)', content.lower())
    if rate_match:
        profile["rate"] = f"${rate_match.group(1)}/hour"
    
    # Determine strengths
    if len(found_skills) >= 6:
        profile["strengths"].append("Strong technical skill set")
    if "react" in text_to_search and "node" in text_to_search:
        profile["strengths"].append("Full MERN stack experience")
    if any(ai in text_to_search for ai in ["ai", "machine learning", "deep learning"]):
        profile["strengths"].append("AI/ML expertise")
    if "upwork.com" in url:
        profile["strengths"].append("Upwork verified profile")
    
    return profile

def calculate_risk_score(profile: Dict[str, Any], content: str) -> int:
    """
    Calculate risk score from 1 (low risk) to 5 (high risk)
    """
    risk_score = 3  # Default to medium risk

    #Reduce risk for positive factors
    if len(profile.get("skills", [])) >= 6:
        risk_score -= 1 # Strong skill set
    if "AI" in profile.get("skills", []) or "Machine Learning" in profile.get("skills", []):
        risk_score -= 1 # AI expertise
    if profile.get("rating", "").startswith(("4", "5")):
        risk_score -= 0.5  # High rating
    
    if "experience" in profile and any(num in profile["experience"] for num in ["3", "4", "5", "6", "7", "8", "9"]):
        risk_score -= 0.5  # Good experience
    
    # Increase risk for negative factors
    if len(profile.get("skills", [])) < 3:
        risk_score += 1  # Limited skills
    
    if "Unknown" in [profile.get("experience", ""), profile.get("rating", "")]:
        risk_score += 0.5  # Missing information
    
    # Ensure score is within bounds
    risk_score = max(1, min(5, int(round(risk_score))))
    
    return risk_score

def get_risk_level(score: int) -> str:
    """Convert numeric risk score to descriptive level"""
    levels = {
        1: "Very Low Risk",
        2: "Low Risk", 
        3: "Medium Risk",
        4: "High Risk",
        5: "Very High Risk"
    }
    return levels.get(score, "Unknown Risk")

# ==================== FINAL RECOMMENDATION AGENT ====================

def final_recommendation_agent(state: DeveloperSearchState) -> DeveloperSearchState:
    """
    Agent 4: Creates final recommendations and rankings
    """
    print("Running Final Recommendation Agent...")
    print("=" * 50)

    evaluated_developers = state.get("evaluated_developers", [])

    if not evaluated_developers:
        print("❌ No developers to recommend.")
        state["final_recommendations"] = []
        state["current_step"] = "final_recommendation_complete"
        return state
    
    #Sort developers by risk score (ascending)

    sorted_developers = sorted(
        evaluated_developers,
        key=lambda x: (x["risk_score"], -len(x["skills"]))  # Sort by risk score, then by number of skills
        )
    
    #Select top 5 developers
    top_5 = sorted_developers[:5]

    print(f"🏆 Top {len(top_5)} Recommended Developers:")

    for i, dev in enumerate(top_5, 1):
        print(f"\n{i}. {dev['name']}")
        print(f"   🎯 Risk Level: {dev['risk_level']} (Score: {dev['risk_score']}/5)")
        print(f"   💼 Skills: {', '.join(dev['skills'][:5])}")
        print(f"   ⭐ Rating: {dev['rating']}")
        print(f"   💰 Rate: {dev['hourly_rate']}")
        print(f"   🔗 Profile: {dev['profile_url']}")
        print(f"   ✅ Strengths: {', '.join(dev['strengths'])}")

    state["final_recommendations"] = top_5
    state["current_step"] = "recommendations_complete"
    
    # Add final summary to messages
    summary = f"Analysis complete! Found {len(top_5)} qualified MERN + AI developers. "
    summary += f"Best candidate: {top_5[0]['name']} with {top_5[0]['risk_level']} rating."
    
    state["messages"].append(AIMessage(content=summary))
    
    print(f"\n✅ Final recommendations ready! Best match: {top_5[0]['name']}")

    
    return state


# ==================== WORKFLOW CREATION ====================

def create_developer_search_workflow():
    """
    Create the complete multi-agent workflow
    """
    print("🏗️  Building Multi-Agent Developer Search Workflow...")

    # Initialize the workflow
    workflow = StateGraph(DeveloperSearchState)

    # Add all agent nodes
    workflow.add_node("search_refinement", search_refinement_agent)
    workflow.add_node("tavily_search", tavily_search_agent)
    workflow.add_node("risk_assessment", risk_assessment_agent) 
    workflow.add_node("recommendation_agent", final_recommendation_agent)

    # Define the workflow sequence
    workflow.set_entry_point("search_refinement")
    workflow.add_edge("search_refinement", "tavily_search")
    workflow.add_edge("tavily_search", "risk_assessment")
    workflow.add_edge("risk_assessment", "recommendation_agent")
    workflow.add_edge("recommendation_agent", END)

    print("✅ Workflow built successfully!")
    return workflow.compile()

# ==================== MAIN EXECUTION FUNCTION ====================

def find_mern_ai_developers(user_request: str):
    """
    Main function to execute the complete developer search workflow
    """
    print("🚀 MERN + AI DEVELOPER SEARCH SYSTEM INITIATED")
    print("=" * 70)
    print(f"📝 User Request: {user_request}")
    print("=" * 70)
    
    # Create workflow
    app = create_developer_search_workflow()
    
    # Initial state
    initial_state = {
        "user_request": user_request,
        "refined_search_query": "",
        "search_keywords": [],
        "raw_search_results": {},
        "evaluated_developers": [],
        "final_recommendations": [],
        "messages": [HumanMessage(content=user_request)],
        "current_step": "initialized"
    }

    try:
        # Execute the complete workflow
        final_state = app.invoke(initial_state)
        
        print("\n" + "=" * 70)
        print("🎉 SEARCH MISSION ACCOMPLISHED!")
        print("=" * 70)
        
        # Display final summary
        recommendations = final_state.get("final_recommendations", [])
        if recommendations:
            print(f"✅ Successfully found {len(recommendations)} qualified developers")
            print(f"🏆 Top recommendation: {recommendations[0]['name']}")
            print(f"⚡ Average risk level: {sum(d['risk_score'] for d in recommendations)/len(recommendations):.1f}/5")
        else:
            print("⚠️  No suitable developers found. Try refining search criteria.")
        
        return final_state
        
    except Exception as e:
        print(f"\n❌ SYSTEM ERROR: {str(e)}")
        return None
    
# ==================== INTERACTIVE EXECUTION ====================
if __name__ == "__main__":
    print("🤖 MERN + AI Developer Search Agent")
    print("Powered by Multi-Agent LangGraph Workflow")
    print("=" * 50)
    
    # Example requests
    test_requests = [
        "Find me 5 MERN Stack developers who know AI",
        "I need full-stack JavaScript developers with machine learning experience",
        "Search for React, Node.js developers who can work with artificial intelligence"
    ]
    
    print("\n📋 Example requests:")
    for i, req in enumerate(test_requests, 1):
        print(f"  {i}. {req}")
    
    # Interactive mode
    while True:
        print("\n" + "─" * 50)
        user_input = input("🔎 Enter your developer search request (or 'quit' to exit): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye! Happy hiring!")
            break
            
        if user_input:
            result = find_mern_ai_developers(user_input)
            
            if result and result.get("final_recommendations"):
                print(f"\n💡 Quick Summary:")
                top_dev = result["final_recommendations"][0]
                print(f"   Best Match: {top_dev['name']}")
                print(f"   Risk Level: {top_dev['risk_level']}")
                print(f"   Key Skills: {', '.join(top_dev['skills'][:3])}")
        else:
            print("⚠️  Please enter a valid search request.")