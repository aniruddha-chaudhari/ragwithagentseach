import json
import os
from typing import Dict, Any, Optional, Union, Tuple

import google.generativeai as genai
from agno.agent import Agent
from agno.models.google import Gemini

# Set up Gemini API key
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD4lR1WQ1yaZumSFtMVTG_0Y8d0oRy1XhA")
genai.configure(api_key='AIzaSyD4lR1WQ1yaZumSFtMVTG_0Y8d0oRy1XhA')


def get_url_detector_agent() -> Agent:
    """Initialize a URL detection agent."""
    return Agent(
        name="URL Detector",
        model=Gemini(id="gemini-2.0-flash"),
        instructions="""You are an expert at identifying URLs in user queries.
        
        Your task is to:
        1. Analyze the user's input
        2. Identify if there is a URL present (http, https, or www formats)
        3. Extract the complete URL and the actual question
        4. Return a structured JSON response with:
           - "url": the full extracted URL
           - "query": the actual question without the URL
        
        If no URL is detected, return:
        {"url": null, "query": "original question"}
        
        Return ONLY the JSON object without any additional text or explanations.
        """,
        show_tool_calls=False,
        markdown=True,
    )


def test_url_detector(query: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Test the URL detector agent with a given query.
    
    Args:
        query (str): The query to test
        verbose (bool): Whether to print detailed results
        
    Returns:
        Dict[str, Any]: Parsed JSON result with url and query fields
    """
    if verbose:
        print(f"\nTesting query: '{query}'")
    
    agent = get_url_detector_agent()
    response = agent.run(query)
    
    try:
        result = json.loads(response.content)
        
        if verbose:
            print(f"URL detected: {result['url'] or 'None'}")
            print(f"Extracted query: '{result['query']}'")
            
        return result
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {response.content}")
        return {"url": None, "query": query, "error": "JSON parse error"}


if __name__ == "__main__":
    # Test cases
    test_queries = [
        "what is happening in next update https://gamerant.com/genshin-impact-event-banners-version-5-4-leak/",
        "explain the concept in https://en.wikipedia.org/wiki/Quantum_entanglement please",
        "can you summarize www.example.com/article for me?",
        "what is the weather today?",
        "check this out: http://tiny.url/abc123 - what do you think?",
    ]
    
    print("=== URL Detector Agent Test ===")
    
    for query in test_queries:
        result = test_url_detector(query, verbose=True)
        print("-" * 50)
    
    # Custom input test
    print("\nEnter your own query to test (Ctrl+C to exit):")
    try:
        while True:
            user_query = input("> ")
            if not user_query:
                break
            result = test_url_detector(user_query, verbose=True)
            print("-" * 50)
    except KeyboardInterrupt:
        print("\nExiting...")
