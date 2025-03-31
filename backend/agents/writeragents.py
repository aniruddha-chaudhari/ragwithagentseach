from agno.agent import Agent
from agno.models.google import Gemini
from typing import Dict, Any, List
from pydantic import BaseModel
from google.genai import types
from google import genai
import json
import re
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY not found in environment variables")

def get_query_rewriter_agent() -> Agent:
    """Initialize a query rewriting agent."""
    return Agent(
        name="Query Rewriter",
        model=Gemini(id="gemini-2.0-flash"),
        instructions="""You are an expert at reformulating questions to be more precise and detailed. 
        Your task is to:
        1. Analyze the user's question
        2. Rewrite it to be more specific and search-friendly
        3. Expand any acronyms or technical terms
        4. Return ONLY the rewritten query without any additional text or explanations
        
        """,
        show_tool_calls=False,
        markdown=True,
    )


def get_rag_agent() -> Agent:
    """Initialize the main RAG agent."""
    return Agent(
        name="Gemini RAG Agent",
        model=Gemini(id="gemini-2.0-flash"),
        instructions="""You are an Intelligent Agent specializing in providing accurate answers.
        
        When given context from documents:
        - Focus on information from the provided documents
        - Be precise and cite specific details
        
        When given web search results:
        - Clearly indicate that the information comes from Google Search
        - Synthesize the information clearly
        - Reference the provided source links when possible
        
        Always maintain high accuracy and clarity in your responses.
        """,
        show_tool_calls=True,
        markdown=True,
    )


def get_baseline_agent() -> Agent:
    """Initialize a baseline agent that uses only internal knowledge without external tools."""
    return Agent(
        name="Baseline Agent",
        model=Gemini(id="gemini-2.0-flash"),
        instructions="""You are an assistant that answers questions using ONLY your internal knowledge.
        
        Important instructions:
        - Do NOT reference any external documents, web searches, or other tools
        - Begin your response with "Based solely on my internal knowledge:"
        - Provide the best information you can, but acknowledge limitations when appropriate
        - If you're unsure or don't have enough information, state this clearly
        - Do NOT pretend to have current or specialized information you don't possess
        
        Your purpose is to demonstrate how AI responds without access to additional information sources.
        """,
        show_tool_calls=False,
        markdown=True,
    )


def get_session_title_generator() -> Agent:
    """Initialize a session title generator agent."""
    return Agent(
        name="Session Title Generator",
        model=Gemini(id="gemini-2.0-flash"),
        instructions="""You are an expert at creating short, concise titles.
        
        Your task is to:
        1. Read the provided user query
        2. Generate a short, descriptive title (4-5 words maximum)
        3. Make the title clearly represent the topic or question
        4. Return ONLY the title without any additional text or explanations
        
        """,
        show_tool_calls=False,
        markdown=True,
    )

def generate_session_title(query: str) -> str:
    """
    Generate a concise title (4-5 words) based on the user's query.
    
    Args:
        query (str): The user's query to base the title on
        
    Returns:
        str: A concise 4-5 word title
    """
    try:
        title_agent = get_session_title_generator()
        title = title_agent.run(f"Generate a concise 4-5 word title for this query: {query}").content
        return title.strip()
    except Exception as e:
        return "Untitled Session"

client = genai.Client(api_key=GEMINI_API_KEY)
class UrldetectionResult(BaseModel):
    urls: List[str]
    query: str
    
def test_url_detector(query: str) -> UrldetectionResult:
    """
    Detect URLs in a user query using both AI and regex approaches.
    
    Args:
        query (str): The query to test
        
    Returns:
        UrldetectionResult: Object with urls list and query fields
    """
    # First try regex-based URL detection as a fallback
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+|'
        r'www\.(?:[a-zA-Z0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    regex_urls = url_pattern.findall(query)

    try:
        # Use the GenerativeModel class for AI-based detection
        prompt = f"""You are an expert at identifying URLs in user queries.
        
        Your task is to:
        1. Analyze the following user input
        2. Identify ALL URLs present (http, https, or www formats)
        3. Extract ALL complete URLs and the actual question
        4. Return a structured JSON response with:
           - "urls": an array of all extracted URLs (empty array if none found)
           - "query": the actual question without the URLs
        
        If no URLs are detected, return:
        {{"urls": [], "query": "original question"}}
        
        Return ONLY the JSON object without any additional text or explanations.
        
        User input: {query}
        """
         
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0.2,
                tools=[types.Tool(
                    google_search=types.GoogleSearchRetrieval()
                )]
            )
        )
        
        
        # Parse the response JSON
        if hasattr(response, 'text'):
            try:
                # Clean the response text in case it has markdown formatting
                clean_text = response.text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                
                result_json = json.loads(clean_text.strip())
                ai_detected = UrldetectionResult(**result_json)
                
                # Combine AI and regex results, prioritizing AI detection
                all_urls = list(set(ai_detected.urls + regex_urls))
                
                # Validate URLs (ensure they start with http/https/www)
                validated_urls = []
                for url in all_urls:
                    if url.startswith(('http://', 'https://')):
                        validated_urls.append(url)
                    elif url.startswith('www.'):
                        validated_urls.append('https://' + url)
                    else:
                        # Try to fix common URL issues
                        if re.match(r'^[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.?', url):
                            validated_urls.append('https://' + url)
                
                return UrldetectionResult(urls=validated_urls, query=ai_detected.query)
            except json.JSONDecodeError as e:
                # Fall back to regex results if JSON parsing fails
                print(f"JSON parsing error in URL detection: {e}. Raw response: {response.text}")
                return UrldetectionResult(urls=regex_urls, query=query)
        else:
            return UrldetectionResult(urls=regex_urls, query=query)
            
    except Exception as e:
        print(f"URL detection error: {str(e)}")
        # Fall back to regex-based detection on error
        return UrldetectionResult(urls=regex_urls, query=query)

def get_curriculum_modifier_agent() -> Agent:
    """Initialize an agent for modifying curriculum structure."""
    return Agent(
        name="Curriculum Modifier",
        model=Gemini(id="gemini-2.0-flash"),
        instructions="""You are an expert educational curriculum designer specializing in modifying existing curricula.

        Your task is to:
        1. Review the existing curriculum structure
        2. Apply the user's requested modifications
        3. Ensure the curriculum maintains logical flow and progression
        4. Return a modified JSON structure that maintains the original format
        
        Return ONLY the JSON object without any additional text or explanations.
        """,
        show_tool_calls=False,
        markdown=True,
    )

def modify_curriculum(curriculum, user_input: str) -> dict:
    """
    Modify a curriculum structure based on user input using Agno agent.
    
    Args:
        curriculum: The existing curriculum overview object
        user_input: The user's modification request
        
    Returns:
        dict: Modified curriculum data 
    """
    try:
        # Get the curriculum modifier agent
        modifier_agent = get_curriculum_modifier_agent()
        
        # Create a prompt that explains the current curriculum and asks for modifications
        prompt = f"""
        Here is a curriculum overview:
        
        Title: {curriculum.title}
        Overview: {curriculum.overview}
        Total Time: {curriculum.total_time}
        
        Current learning steps:
        {json.dumps([{"title": step.title, "estimated_time": step.estimated_time} for step in curriculum.steps])}
        
        The user wants to modify this curriculum with the following request:
        "{user_input}"
        
        Based on this request, update the curriculum steps.
        Return only a JSON object with this structure:
        {{
          "steps": [
            {{
              "title": "Step Title",
              "estimated_time": "X hours/weeks"
            }}
          ]
        }}
        """
        
        # Use the agent to process the modification
        response = modifier_agent.run(prompt)
        
        # Get the response content
        response_text = response.content
        
        # Clean up the response if needed (e.g., removing markdown code block markers)
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        # Parse JSON
        modified_data = json.loads(response_text.strip())
        return modified_data
        
    except Exception as e:
        # Return default data structure if there's an error
        return {"steps": [{"title": step.title, "estimated_time": step.estimated_time} for step in curriculum.steps]}