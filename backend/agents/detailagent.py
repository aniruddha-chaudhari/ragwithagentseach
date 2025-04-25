from agno.agent import Agent
from agno.models.google import Gemini
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import os
import json
import traceback
from google import genai

# Import search functionality
from search import google_search

class SectionDetailInput(BaseModel):
    """Input model for detailed knowledge section generation"""
    section_title: str
    estimated_time: str
    topic: str = ""
    user_preferences: Optional[str] = None

class DetailedSection(BaseModel):
    """Model for the detailed knowledge section"""
    section_title: str
    estimated_time: str
    key_points: List[str] = Field(default_factory=list)
    subtopics: List[str] = Field(default_factory=list)
    core_concepts: str = ""
    information_sources: List[Dict[str, str]] = Field(default_factory=list)
    practical_applications: List[Dict[str, str]] = Field(default_factory=list)
    verification_methods: str = ""
    advanced_exploration: List[str] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(default_factory=dict)

def get_detail_generator_agent() -> Agent:
    """Initialize a detailed knowledge section generator agent"""
    return Agent(
        name="Knowledge Detail Generator",
        model=Gemini(id="gemini-2.0-flash"),
        instructions="""You are an expert researcher specializing in creating 
        detailed, comprehensive knowledge resources. Your task is to expand a 
        knowledge section into detailed content.

        When given a section title and estimated time, create comprehensive detailed content that includes:
        - 3-5 key points the reader should understand about this section
        - Subtopics that should be explored within this section
        - Brief overview of core concepts (keep minimal as we now have subtopics)
        - Information sources (identified through search) with mix of types (articles, academic papers, videos)
          labeled as authoritative or supplementary
        - Practical applications of this knowledge with real-world examples
        - Verification methods explaining how the information can be validated
        - Advanced exploration areas for deeper understanding
        - Relationships to other knowledge areas and topics

        Make content educational, accurate, and engaging, focusing on both theoretical understanding 
        and practical applications. Ensure content is comprehensive but appropriate for the estimated time frame.

        Format your response as a structured JSON object with all the above sections.
        """,
        show_tool_calls=True,
        markdown=True,
    )

def generate_section_detail(input_data: SectionDetailInput) -> DetailedSection:
    """
    Generate detailed content for a knowledge section
    
    Args:
        input_data: The input data containing section title, estimated time, etc.
        
    Returns:
        DetailedSection: The detailed knowledge section
    """
    try:
        # Perform an initial search to gather context and sources
        search_results = ""
        source_links = []
        
        try:
            print(f"Searching for sources on: {input_data.section_title}")
            # First search for general content on the topic
            search_query = f"{input_data.section_title} research sources"
            if input_data.topic:
                search_query += f" {input_data.topic}" 
                
            search_text, links = google_search(search_query)
            if search_text:
                search_results = f"\nSearch Results for Information Sources:\n{search_text}"
                source_links = links
                print(f"Found {len(links)} source links")
        except Exception as e:
            print(f"Error performing search for sources: {e}")
        
        # Use Gemini API to generate the detailed content
        api_key = os.getenv("GEMINI_API_KEY", "")
        client = genai.Client(api_key=api_key)
        
        # Create a prompt for Gemini
        detail_prompt = f"""
        You are an expert researcher specializing in creating detailed, comprehensive knowledge resources.
        Your task is to expand a knowledge section into detailed content.

        **Input:**
        - Section title: {input_data.section_title}
        - Estimated time to comprehend: {input_data.estimated_time}
        - Main topic: {input_data.topic}
        - User preferences: {input_data.user_preferences or "None provided"}
        
        {search_results}
        
        **Output Requirements:**
        - Generate 3-5 key points that readers should understand from this section based on the section title and complexity.
        - Create comprehensive detailed content for the knowledge section, with the following parts:
          - Subtopics: List specific subtopics that should be explored within this section.
          - Information Sources: Use the search results to curate a list of the top 3-5 sources, ensuring a mix of types (articles, academic papers, videos). Label which are authoritative vs. supplementary.
          - Practical Applications: Provide 3-5 real-world applications of this knowledge with specific examples.
          - Verification Methods: Explain how information in this section can be validated or tested.
          - Advanced Exploration: Suggest deeper or related topics for further exploration.
        - Incorporate any user preferences if provided.

        Generate detailed educational content in JSON format with the following structure:
        {{
          "key_points": ["point1", "point2", "point3"],
          "subtopics": ["subtopic1", "subtopic2", "subtopic3"],
          "core_concepts": "Brief overview of core concepts (keep minimal as we now have subtopics)",
          "information_sources": [
            {{"title": "Source title", "url": "url", "description": "Brief description", "type": "authoritative/supplementary"}}
          ],
          "practical_applications": [
            {{"title": "Application example", "description": "Description of how this knowledge applies to real-world scenarios", "context": "academic/industry/everyday"}}
          ],
          "verification_methods": "Description of how to validate or test this information",
          "advanced_exploration": ["topic1", "topic2", "topic3"],
          "relationships": {{
            "prerequisite": "Knowledge this builds upon",
            "related": "Connected knowledge areas"
          }}
        }}
        
        Ensure the information sources include these URLs when relevant: {json.dumps(source_links)}
        Use formatting (bullet points, section headings) to make content digestible.
        Ensure content is appropriately complex for the estimated time frame.
        Make the content educational, accurate, and engaging, focusing on both theoretical understanding and practical applications.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=detail_prompt,
            config={
                'response_mime_type': 'application/json'
            }
        )
        
        # Process the response
        response_text = response.text
        
        # Clean up the response if needed
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        # Parse JSON
        detail_data = json.loads(response_text.strip())
        
        # Create the detailed section
        detailed_section = DetailedSection(
            section_title=input_data.section_title,
            estimated_time=input_data.estimated_time,
            key_points=detail_data.get("key_points", []),
            subtopics=detail_data.get("subtopics", []),
            core_concepts=detail_data.get("core_concepts", ""),
            information_sources=detail_data.get("information_sources", []),
            practical_applications=detail_data.get("practical_applications", []),
            verification_methods=detail_data.get("verification_methods", ""),
            advanced_exploration=detail_data.get("advanced_exploration", []),
            relationships=detail_data.get("relationships", {})
        )
        
        # Print confirmation of generated content
        print(f"Successfully generated detailed content for section: {input_data.section_title}")
        print(f"Contains {len(detailed_section.key_points)} key points and {len(detailed_section.subtopics)} subtopics")
        
        return detailed_section
    
    except Exception as e:
        print(f"Error generating section detail: {e}\n{traceback.format_exc()}")
        
        # Create a minimal fallback response
        return DetailedSection(
            section_title=input_data.section_title,
            estimated_time=input_data.estimated_time,
            key_points=["Understand key concepts", "Apply knowledge", "Develop critical thinking skills"],
            subtopics=["Introduction", "Primary Concepts", "Practical Applications"],
            core_concepts="Content generation failed. Please try again.",
            information_sources=[],
            practical_applications=[],
            verification_methods="Standard research validation methods and critical analysis.",
            advanced_exploration=["Further research in this area"],
            relationships={"prerequisite": "Foundational knowledge", "related": "Connected topics"}
        )

def format_detailed_section_text(detailed_section: DetailedSection) -> str:
    """
    Format the detailed section as human-readable markdown text
    
    Args:
        detailed_section: The detailed knowledge section object
        
    Returns:
        str: Formatted text representation of the detailed section
    """
    text = f"# {detailed_section.section_title}\n\n"
    text += f"**Estimated Time to Comprehend:** {detailed_section.estimated_time}\n\n"
    
    # Key Points
    text += "## Key Points\n\n"
    for i, point in enumerate(detailed_section.key_points, 1):
        text += f"{i}. {point}\n"
    text += "\n"
    
    # Subtopics
    text += "## Subtopics\n\n"
    for i, subtopic in enumerate(detailed_section.subtopics, 1):
        text += f"- {subtopic}\n"
    text += "\n"
    
    # Core Concepts
    text += "## Overview of Core Concepts\n\n"
    text += f"{detailed_section.core_concepts}\n\n"
    
    # Information Sources
    text += "## Information Sources\n\n"
    for i, source in enumerate(detailed_section.information_sources, 1):
        source_type = source.get("type", "")
        type_label = f" ({source_type})" if source_type else ""
        text += f"{i}. [{source.get('title', 'Source')}]({source.get('url', '#')}){type_label}\n"
        text += f"   {source.get('description', '')}\n\n"
    
    # Practical Applications
    text += "## Practical Applications\n\n"
    for i, application in enumerate(detailed_section.practical_applications, 1):
        context = application.get("context", "")
        context_label = f" (Context: {context})" if context else ""
        text += f"### Application {i}: {application.get('title', '')}{context_label}\n\n"
        text += f"{application.get('description', '')}\n\n"
    
    # Verification Methods
    text += "## Verification Methods\n\n"
    text += f"{detailed_section.verification_methods}\n\n"
    
    # Advanced Exploration
    text += "## Advanced Topics for Further Exploration\n\n"
    for topic in detailed_section.advanced_exploration:
        text += f"- {topic}\n"
    text += "\n"
    
    # Relationships
    text += "## Relationships to Other Knowledge Areas\n\n"
    text += f"**Prerequisites:** {detailed_section.relationships.get('prerequisite', 'None')}\n\n"
    text += f"**Related Areas:** {detailed_section.relationships.get('related', 'None')}\n\n"
    
    return text

if __name__ == "__main__":
    # Example usage for testing
    test_input = SectionDetailInput(
        section_title="Quantum Computing Fundamentals",
        estimated_time="3 days",
        topic="Quantum Computing"
    )
    
    result = generate_section_detail(test_input)
    formatted_text = format_detailed_section_text(result)
    
    print("DETAILED SECTION GENERATION COMPLETE")
    print(formatted_text)
