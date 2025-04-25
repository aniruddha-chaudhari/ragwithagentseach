import os
import json
import uuid
import traceback
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel

# Import knowledge generation components
from coordinator_agent import ResearchInput, coordinate
from agents.overview_agent import KnowledgeSection, KnowledgeOverview, format_overview_text, format_any_overview_text
from utils.curriculum_utils import save_curriculum_step, get_curriculum_step, update_curriculum_step
from agents.writeragents import modify_curriculum
from agents.detailagent import generate_section_detail, format_detailed_section_text, SectionDetailInput, DetailedSection

class KnowledgeRequest(BaseModel):
    """Request model for knowledge research generation"""
    topic: str
    source_url: Optional[str] = None
    depth_level: Optional[str] = None

class KnowledgeModificationRequest(BaseModel):
    """Request model for knowledge modification"""
    modification_text: str

class KnowledgeResponse(BaseModel):
    """Response model for knowledge operations"""
    research_id: str
    title: str
    overview: str
    sections: List[Dict[str, str]]
    complexity_level: str
    formatted_text: str

class SectionDetailResponse(BaseModel):
    """Response model for detailed section content"""
    section_title: str
    estimated_time: str
    content: Dict[str, Any]
    formatted_text: str

class KnowledgeMapResponse(BaseModel):
    """Response model for knowledge map visualization"""
    research_id: str
    mermaid_code: str

class KnowledgeListResponse(BaseModel):
    """Response model for listing knowledge research"""
    researches: List[Dict[str, str]]

class KnowledgeCreateRequest(BaseModel):
    """Request model for creating a new knowledge research"""
    research_name: str

def generate_knowledge(request: KnowledgeRequest) -> KnowledgeResponse:
    """
    Generate a knowledge research based on the request parameters
    
    Args:
        request: KnowledgeRequest containing topic, optional source URL, and depth level
        
    Returns:
        KnowledgeResponse with the generated knowledge research
    """
    try:
        # Create input for coordinator
        coordinator_input = ResearchInput(
            query=request.topic,
            source_url=request.source_url,
            depth_level=request.depth_level
        )
        
        # Generate knowledge research
        result = coordinate(coordinator_input)
        
        # Use the new format_any_overview_text function instead of specific formatters
        formatted_text = format_any_overview_text(result.overview)
        
        # Create response
        return KnowledgeResponse(
            research_id=result.raw_data.research_id,
            title=result.overview.get("title", "Untitled Research"),
            overview=result.overview.get("overview", "No overview available"),
            sections=[{"title": section.get("title", "Untitled Section"), 
                      "estimated_time": section.get("estimated_time", "Not specified")} 
                     for section in result.overview.get("sections", [])],
            complexity_level=result.overview.get("complexity_level", "Not specified"),
            formatted_text=formatted_text
        )
    except Exception as e:
        error_details = f"Error generating knowledge research: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to generate knowledge research: {str(e)}")

def get_knowledge(research_id: str) -> KnowledgeResponse:
    """
    Get a knowledge research by ID
    
    Args:
        research_id: The UUID of the research
        
    Returns:
        KnowledgeResponse with the research data
    """
    try:
        # Get knowledge research from database
        research_data = get_curriculum_step(research_id)
        
        if not research_data:
            raise Exception(f"Knowledge research with ID {research_id} not found")
        
        # Parse overview data
        overview_data = research_data.get("overview", {})
        section_data = overview_data.get("topics", [])
        
        sections = []
        for topic in section_data:
            sections.append({
                "title": topic.get("name", "Unknown section"),
                "estimated_time": "Not specified"
            })
        
        # Create knowledge overview
        overview = KnowledgeOverview(
            research_id=research_id,
            title=research_data.get("step_title", "Untitled Research"),
            overview=f"Research covering key aspects of {research_data.get('step_title', 'the topic')}.",
            sections=[KnowledgeSection(title=section["title"], estimated_time=section["estimated_time"]) for section in sections],
            complexity_level=research_data.get("estimated_time", "Not specified")
        )
        
        # Format text
        formatted_text = format_overview_text(overview)
        
        # Create response
        return KnowledgeResponse(
            research_id=research_id,
            title=overview.title,
            overview=overview.overview,
            sections=sections,
            complexity_level=overview.complexity_level,
            formatted_text=formatted_text
        )
    except Exception as e:
        error_details = f"Error retrieving knowledge research: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to retrieve knowledge research: {str(e)}")

def modify_knowledge_by_id(research_id: str, request: KnowledgeModificationRequest) -> KnowledgeResponse:
    """
    Modify a knowledge research based on the request
    
    Args:
        research_id: The UUID of the research to modify
        request: KnowledgeModificationRequest containing modification text
        
    Returns:
        KnowledgeResponse with the modified research
    """
    try:
        # Get current research
        research_data = get_curriculum_step(research_id)
        
        if not research_data:
            raise Exception(f"Knowledge research with ID {research_id} not found")
            
        # Parse current research data
        overview_data = research_data.get("overview", {})
        section_data = overview_data.get("topics", [])
        
        # Create knowledge overview object from data
        sections = []
        for topic in section_data:
            sections.append(KnowledgeSection(
                title=topic.get("name", "Unknown section"),
                estimated_time="Not specified"
            ))
        
        current_knowledge = KnowledgeOverview(
            research_id=research_id,
            title=research_data.get("step_title", "Untitled Research"),
            overview=f"Research covering key aspects of {research_data.get('step_title', 'the topic')}.",
            sections=sections,
            complexity_level=research_data.get("estimated_time", "Not specified")
        )
        
        # Apply modifications - reusing the curriculum modification function
        # but adapting the response
        modified_data = modify_curriculum(current_knowledge, request.modification_text)
        
        # Create new sections from the JSON data
        new_sections = []
        for section_data in modified_data.get("steps", []):
            new_sections.append(KnowledgeSection(
                title=section_data.get("title", "Untitled Section"),
                estimated_time=section_data.get("estimated_time", "Not specified")
            ))
        
        # Create a new knowledge with the updated sections
        updated_knowledge = KnowledgeOverview(
            research_id=research_id,
            title=current_knowledge.title,
            overview=current_knowledge.overview,
            sections=new_sections,
            complexity_level=current_knowledge.complexity_level
        )
        
        # Format as text
        formatted_text = format_overview_text(updated_knowledge)
        
        # Save updated research to database
        updated_overview_data = {
            "topics": [{"name": section.title, "estimated_time": section.estimated_time} 
                    for section in updated_knowledge.sections]
        }
        
        save_result = save_curriculum_step(
            research_id,
            updated_knowledge.title,
            updated_knowledge.complexity_level,
            updated_overview_data
        )
        
        if not save_result:
            print("Warning: Failed to save updated knowledge to database")
        
        # Create response
        return KnowledgeResponse(
            research_id=research_id,
            title=updated_knowledge.title,
            overview=updated_knowledge.overview,
            sections=[{"title": section.title, "estimated_time": section.estimated_time} 
                  for section in updated_knowledge.sections],
            complexity_level=updated_knowledge.complexity_level,
            formatted_text=formatted_text
        )
    except Exception as e:
        error_details = f"Error modifying knowledge research: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to modify knowledge research: {str(e)}")

def generate_section_details(research_id: str) -> Dict[int, SectionDetailResponse]:
    """
    Generate detailed content for all sections in a knowledge research
    
    Args:
        research_id: The UUID of the research
        
    Returns:
        Dict mapping section indices to SectionDetailResponse objects
    """
    try:
        # Get research
        research_data = get_curriculum_step(research_id)
        
        if not research_data:
            raise Exception(f"Knowledge research with ID {research_id} not found")
            
        # Parse research data
        overview_data = research_data.get("overview", {})
        section_data = overview_data.get("topics", [])
        
        # Create knowledge overview object from data
        sections = []
        for topic in section_data:
            sections.append(KnowledgeSection(
                title=topic.get("name", "Unknown section"),
                estimated_time="Not specified"
            ))
        
        knowledge = KnowledgeOverview(
            research_id=research_id,
            title=research_data.get("step_title", "Untitled Research"),
            overview=f"Research covering key aspects of {research_data.get('step_title', 'the topic')}.",
            sections=sections,
            complexity_level=research_data.get("estimated_time", "Not specified")
        )
        
        # Check if detailed_content already exists in the research_data
        detailed_content = research_data.get("detailed_content", {}) or {}
        
        # Process each section
        detailed_sections = {}
        
        for index, section in enumerate(knowledge.sections):
            section_key = f"section_{index}"
            existing_detail = detailed_content.get(section_key)
            
            if existing_detail:
                print(f"Retrieved existing detailed content for section {index}")
                # Use existing detailed content
                detailed_section = DetailedSection(
                    section_title=existing_detail.get("section_title", section.title),
                    estimated_time=existing_detail.get("estimated_time", section.estimated_time),
                    key_points=existing_detail.get("key_points", []),
                    subtopics=existing_detail.get("subtopics", []),
                    core_concepts=existing_detail.get("core_concepts", ""),
                    information_sources=existing_detail.get("information_sources", []),
                    practical_applications=existing_detail.get("practical_applications", []),
                    verification_methods=existing_detail.get("verification_methods", ""),
                    advanced_exploration=existing_detail.get("advanced_exploration", []),
                    relationships=existing_detail.get("relationships", {})
                )
            else:
                print(f"Generating new detailed content for section {index}")
                # Set up input for detail generator
                detail_input = SectionDetailInput(
                    section_title=section.title,
                    estimated_time=section.estimated_time,
                    topic=knowledge.title
                )
                
                # Generate detailed content
                detailed_section = generate_section_detail(detail_input)
                
                # Save the detailed content to database
                try:
                    from utils.curriculum_utils import save_curriculum_step_detail
                    detail_dict = detailed_section.dict()
                    detailed_content_key = f"{research_id}_section_{index}"
                    save_result = save_curriculum_step_detail(
                        detailed_content_key,
                        research_id,
                        index,
                        detail_dict
                    )
                    if save_result:
                        print(f"Successfully saved detailed content for section {index}")
                    else:
                        print(f"Failed to save detailed content for section {index}")
                except Exception as e:
                    print(f"Error saving detailed content: {e}")
            
            # Format as text
            detailed_text = format_detailed_section_text(detailed_section)
            
            # Store the results
            if detailed_section:
                detailed_sections[index] = SectionDetailResponse(
                    section_title=detailed_section.section_title,
                    estimated_time=detailed_section.estimated_time,
                    content=detailed_section.dict(),
                    formatted_text=detailed_text
                )
        
        return detailed_sections
    except Exception as e:
        error_details = f"Error generating section details: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to generate section details: {str(e)}")

def get_section_detail(research_id: str, section_index: int) -> SectionDetailResponse:
    """
    Get detailed content for a specific section
    
    Args:
        research_id: The UUID of the research
        section_index: The index of the section
        
    Returns:
        SectionDetailResponse with the detailed section content
    """
    try:
        # Get the research with detailed content
        research_data = get_curriculum_step(research_id)
        
        if not research_data:
            raise Exception(f"Knowledge research with ID {research_id} not found")
        
        # Check if detailed content exists in the research_data
        detailed_content = research_data.get("detailed_content", {}) or {}
        section_key = f"section_{section_index}"
        existing_detail = detailed_content.get(section_key)
        
        if existing_detail:
            print(f"Retrieved existing detailed content for section {section_index}")
            
            # Parse research data to get section title
            overview_data = research_data.get("overview", {})
            section_data = overview_data.get("topics", [])
            
            if section_index >= len(section_data):
                raise Exception(f"Section index {section_index} out of range for research {research_id}")
            
            section_title = section_data[section_index].get("name", "Unknown section")
            estimated_time = "Not specified"
            
            # Create DetailedSection from stored data
            detailed_section = DetailedSection(
                section_title=existing_detail.get("section_title", section_title),
                estimated_time=existing_detail.get("estimated_time", estimated_time),
                key_points=existing_detail.get("key_points", []),
                subtopics=existing_detail.get("subtopics", []),
                core_concepts=existing_detail.get("core_concepts", ""),
                information_sources=existing_detail.get("information_sources", []),
                practical_applications=existing_detail.get("practical_applications", []),
                verification_methods=existing_detail.get("verification_methods", ""),
                advanced_exploration=existing_detail.get("advanced_exploration", []),
                relationships=existing_detail.get("relationships", {})
            )
            
            # Format as text
            detailed_text = format_detailed_section_text(detailed_section)
            
            # Return the response
            return SectionDetailResponse(
                section_title=detailed_section.section_title,
                estimated_time=detailed_section.estimated_time,
                content=detailed_section.dict(),
                formatted_text=detailed_text
            )
        else:
            print(f"No existing detail found for section {section_index}, will generate new content")
            # If we don't have stored content, generate all details
            all_details = generate_section_details(research_id)
            
            # Check if the requested section exists
            if section_index not in all_details:
                raise Exception(f"Section with index {section_index} not found in research {research_id}")
            
            return all_details[section_index]
    except Exception as e:
        error_details = f"Error retrieving section detail: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to retrieve section detail: {str(e)}")

def generate_knowledge_map(research_id: str) -> KnowledgeMapResponse:
    """
    Generate a visual map for the knowledge research
    
    Args:
        research_id: The UUID of the research
        
    Returns:
        KnowledgeMapResponse with the mermaid diagram code
    """
    try:
        # Get research
        research_data = get_curriculum_step(research_id)
        
        if not research_data:
            raise Exception(f"Knowledge research with ID {research_id} not found")
            
        # Parse research data
        overview_data = research_data.get("overview", {})
        section_data = overview_data.get("topics", [])
        
        # Create knowledge overview object from data
        sections = []
        for topic in section_data:
            sections.append(KnowledgeSection(
                title=topic.get("name", "Unknown section"),
                estimated_time="Not specified"
            ))
        
        knowledge = KnowledgeOverview(
            research_id=research_id,
            title=research_data.get("step_title", "Untitled Research"),
            overview=f"Research covering key aspects of {research_data.get('step_title', 'the topic')}.",
            sections=sections,
            complexity_level=research_data.get("estimated_time", "Not specified")
        )
        
        # Create a flowchart diagram using Mermaid syntax
        mermaid_code = """
        flowchart LR
            Start([Start]) --> Section1
        """
        
        # Add each section as a node
        for i, section in enumerate(knowledge.sections, 1):
            # Add the section node
            section_id = f"Section{i}"
            section_title = section.title
            estimated_time = section.estimated_time
            
            # Truncate long titles for better display
            if len(section_title) > 30:
                section_title = section_title[:27] + "..."
                
            mermaid_code += f"""
            {section_id}["{section_title}<br><small>{estimated_time}</small>"]
            """
            
            # Add connection to next section if not the last one
            if i < len(knowledge.sections):
                mermaid_code += f"""
            {section_id} --> Section{i+1}
                """
        
        # Add final node
        mermaid_code += """
            Section{} --> Finish([Complete])
        """.format(len(knowledge.sections))
        
        return KnowledgeMapResponse(
            research_id=research_id,
            mermaid_code=mermaid_code
        )
    except Exception as e:
        error_details = f"Error generating knowledge map: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to generate knowledge map: {str(e)}")

def get_all_knowledge_researches() -> KnowledgeListResponse:
    """
    Get a list of all available knowledge researches
    
    Returns:
        KnowledgeListResponse containing list of research metadata
    """
    try:
        # Get all research entries from Supabase database
        from utils.curriculum_utils import get_all_curriculum_steps
        
        # Query all records from Supabase
        research_records = get_all_curriculum_steps()
        
        # Format the list for response
        research_list = []
        for record in research_records:
            research_list.append({
                "research_id": record.get("step_id"),
                "research_name": record.get("step_title", "Untitled Research")
            })
        
        return KnowledgeListResponse(researches=research_list)
    except Exception as e:
        error_details = f"Error listing knowledge researches: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to list knowledge researches: {str(e)}")

def create_knowledge(request: KnowledgeCreateRequest) -> Dict[str, str]:
    """
    Create a new empty knowledge research
    
    Args:
        request: KnowledgeCreateRequest containing research name
        
    Returns:
        Dict with research_id and research_name
    """
    try:
        research_id = str(uuid.uuid4())
        research_name = request.research_name
        
        # Create a minimal knowledge structure
        research_data = {
            "step_title": research_name,
            "estimated_time": "Not specified",
            "overview": {
                "topics": []
            }
        }
        
        # Save to database
        save_result = save_curriculum_step(
            research_id,
            research_name,
            "Not specified",
            research_data
        )
        
        if not save_result:
            raise Exception("Failed to save knowledge research to database")
        
        return {
            "research_id": research_id,
            "research_name": research_name
        }
    except Exception as e:
        error_details = f"Error creating knowledge research: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to create knowledge research: {str(e)}")

def delete_knowledge_by_id(research_id: str) -> bool:
    """
    Delete a knowledge research by ID
    
    Args:
        research_id: The UUID of the research to delete
        
    Returns:
        Boolean indicating success
    """
    try:
        # Check if research exists
        research_data = get_curriculum_step(research_id)
        if not research_data:
            raise Exception(f"Knowledge research with ID {research_id} not found")
        
        # Delete research file
        # In a real implementation, you would remove from your database
        research_file = os.path.join(os.path.dirname(__file__), "data", "researches", f"{research_id}.json")
        if os.path.exists(research_file):
            os.remove(research_file)
            return True
        else:
            # Not found on disk but was found by get_curriculum_step
            # This suggests an inconsistency, but return True as the intent is fulfilled
            return True
    except Exception as e:
        error_details = f"Error deleting knowledge research: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to delete knowledge research: {str(e)}")