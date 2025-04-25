import os
import json
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
from google import genai

# Import Google search functionality
from search import google_search

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    # Only imports during type checking, not at runtime
    from coordinator_agent import KnowledgeOutput

class KnowledgeSection(BaseModel):
    """Model for a knowledge section"""
    title: str
    estimated_time: str

class KnowledgeOverview(BaseModel):
    """Model for the complete knowledge overview"""
    research_id: str
    title: str
    overview: str
    sections: List[KnowledgeSection]
    complexity_level: str

# For compatibility with curriculum_service imports
class CurriculumStep(BaseModel):
    """Model for a curriculum step"""
    title: str
    objectives: List[str] = Field(default_factory=list)
    estimated_time: str

class CurriculumOverview(BaseModel):
    """Model for the complete curriculum overview"""
    curriculum_id: str
    title: str
    overview: str
    steps: List[CurriculumStep]
    total_time: str

def generate_overview(coordinator_output: "KnowledgeOutput") -> KnowledgeOverview:
    """
    Generate a simplified knowledge overview from coordinator output
    
    Args:
        coordinator_output: The structured output from the coordinator agent
        
    Returns:
        KnowledgeOverview: The simplified knowledge overview with sections
    """
    # Extract key data from coordinator output
    research_id = coordinator_output.research_id
    topic = coordinator_output.topic
    summary = coordinator_output.summary
    key_concepts = coordinator_output.key_concepts
    knowledge_structure = coordinator_output.knowledge_structure
    depth_metrics = coordinator_output.depth_metrics
    complexity_level = coordinator_output.complexity_level
    
    # Perform additional Google search to enhance knowledge context
    search_results = ""
    try:
        print(f"Performing additional search for knowledge context on: {topic}")
        search_query = f"{topic} research latest understanding"
        search_text, _ = google_search(search_query)
        if search_text:
            search_results = f"\nAdditional context from search:\n{search_text}"
            print("Successfully retrieved additional context from search")
        else:
            print("No additional context retrieved from search")
    except Exception as e:
        print(f"Error performing additional search: {e}")
    
    # Use Gemini API to generate the knowledge overview
    try:
        api_key = os.getenv("GEMINI_API_KEY", "")
        client = genai.Client(api_key=api_key)
        
        # Create a prompt for Gemini using the coordinator data with simplified requirements
        overview_prompt = f"""
        You are an expert researcher and knowledge organizer. Create a simplified knowledge overview 
        for the topic: {topic}
        
        Here are the key concepts and their relationships:
        {json.dumps(key_concepts)}
        
        Here is the suggested knowledge structure:
        {json.dumps(knowledge_structure)}
        
        Complexity level: {complexity_level}
        {search_results}
        
        Generate a knowledge overview with the following:
        1. A concise title for the research overview
        2. A brief overview paragraph (3-5 sentences) describing the topic's importance and structure
        3. 5-10 logical knowledge sections that present information from fundamental to advanced
        4. For each section, provide:
           - A clear, descriptive title
           - Estimated time to comprehend this knowledge section
        
        Format your response as JSON with this structure:
        {{
          "title": "Knowledge Overview Title",
          "overview": "Brief overview paragraph",
          "sections": [
            {{
              "title": "Section Title",
              "estimated_time": "X hours/days to comprehend"
            }}
          ]
        }}
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=overview_prompt,
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
        overview_data = json.loads(response_text.strip())
        
        # Create sections from the JSON data
        sections = []
        for section_data in overview_data.get("sections", []):
            sections.append(KnowledgeSection(
                title=section_data.get("title", "Untitled Section"),
                estimated_time=section_data.get("estimated_time", "Not specified")
            ))
        
        # Create and return the full knowledge overview
        return KnowledgeOverview(
            research_id=research_id,
            title=overview_data.get("title", f"Knowledge Overview for {topic}"),
            overview=overview_data.get("overview", summary),
            sections=sections,
            complexity_level=complexity_level
        )
    
    except Exception as e:
        print(f"Error generating knowledge overview: {e}")
        
        # Create a fallback overview if API call fails
        sections = []
        for i, concept in enumerate(key_concepts[:5], 1):
            sections.append(KnowledgeSection(
                title=concept.get("name", f"Section {i}"),
                estimated_time="2 days"
            ))
        
        return KnowledgeOverview(
            research_id=research_id,
            title=f"Knowledge Overview for {topic}",
            overview=f"This overview covers the fundamentals of {topic}, progressing from basic concepts to advanced applications.",
            sections=sections,
            complexity_level=complexity_level
        )

def format_overview_text(overview: KnowledgeOverview) -> str:
    """
    Format the knowledge overview as a human-readable text
    
    Args:
        overview: The knowledge overview object
        
    Returns:
        str: Formatted text representation of the knowledge
    """
    text = f"# {overview.title}\n\n"
    text += f"## Overview\n{overview.overview}\n\n"
    text += f"**Complexity Level: {overview.complexity_level}**\n\n"
    text += "## Knowledge Sections\n\n"
    
    for i, section in enumerate(overview.sections, 1):
        text += f"### {i}. {section.title}\n"
        text += f"**Estimated Time to Comprehend:** {section.estimated_time}\n\n"
    
    return text

def format_curriculum_text(overview: CurriculumOverview) -> str:
    """
    Format the curriculum overview as a human-readable text
    
    Args:
        overview: The curriculum overview object
        
    Returns:
        str: Formatted text representation of the curriculum
    """
    text = f"# {overview.title}\n\n"
    text += f"## Overview\n{overview.overview}\n\n"
    text += f"**Total Time: {overview.total_time}**\n\n"
    text += "## Learning Steps\n\n"
    
    for i, step in enumerate(overview.steps, 1):
        text += f"### {i}. {step.title}\n"
        text += f"**Estimated Time:** {step.estimated_time}\n"
        if step.objectives:
            text += "**Objectives:**\n"
            for objective in step.objectives:
                text += f"- {objective}\n"
        text += "\n"
    
    return text

def format_any_overview_text(overview) -> str:
    """
    Format either a knowledge overview or curriculum overview as a human-readable text
    
    Args:
        overview: Either a KnowledgeOverview or CurriculumOverview object
        
    Returns:
        str: Formatted text representation
    """
    if hasattr(overview, 'sections'):  # It's a KnowledgeOverview
        return format_overview_text(overview)
    elif hasattr(overview, 'steps'):   # It's a CurriculumOverview
        return format_curriculum_text(overview)
    elif isinstance(overview, dict):   # It's a dictionary representation
        if 'sections' in overview:
            # Convert dict to KnowledgeOverview
            sections = [KnowledgeSection(title=s.get('title', 'Untitled'), 
                                        estimated_time=s.get('estimated_time', 'Not specified')) 
                       for s in overview.get('sections', [])]
            
            temp_overview = KnowledgeOverview(
                research_id=overview.get('research_id', 'unknown'),
                title=overview.get('title', 'Untitled Overview'),
                overview=overview.get('overview', 'No overview available'),
                sections=sections,
                complexity_level=overview.get('complexity_level', 'Not specified')
            )
            return format_overview_text(temp_overview)
        elif 'steps' in overview:
            # Convert dict to CurriculumOverview
            steps = [CurriculumStep(title=s.get('title', 'Untitled'), 
                                  estimated_time=s.get('estimated_time', 'Not specified'),
                                  objectives=s.get('objectives', [])) 
                   for s in overview.get('steps', [])]
            
            temp_overview = CurriculumOverview(
                curriculum_id=overview.get('curriculum_id', 'unknown'),
                title=overview.get('title', 'Untitled Curriculum'),
                overview=overview.get('overview', 'No overview available'),
                steps=steps,
                total_time=overview.get('total_time', 'Not specified')
            )
            return format_curriculum_text(temp_overview)
    
    # Fallback for unknown object types
    return "Could not format overview: unknown overview type"

if __name__ == "__main__":
    # For testing purposes
    from coordinator_agent import ResearchInput, coordinate
    
    test_input = ResearchInput(
        query="Quantum Computing",
        depth_level="Advanced"
    )
    
    coordinator_result = coordinate(test_input)
    overview_result = generate_overview(coordinator_result.raw_data)
    
    print("Overview Generation Complete!")
    print(f"Title: {overview_result.title}")
    print(f"Overview: {overview_result.overview}")
    print("\nSections:")
    for i, section in enumerate(overview_result.sections, 1):
        print(f"{i}. {section.title}")
        print(f"   Estimated Time: {section.estimated_time}")
    
    # Print formatted text version
    print("\nFormatted Overview:")
    print(format_overview_text(overview_result))
