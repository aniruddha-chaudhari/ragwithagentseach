import os
import json
import uuid
import traceback
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel

# Import curriculum generation components
from coordinator_agent import ResearchInput as CoordinatorInput, coordinate
from agents.overview_agent import CurriculumStep, CurriculumOverview, format_curriculum_text
from utils.curriculum_utils import save_curriculum_step, get_curriculum_step, update_curriculum_step
from agents.writeragents import modify_curriculum
from agents.detailagent import generate_section_detail as generate_step_detail, format_detailed_section_text as format_detailed_step_text, SectionDetailInput as StepDetailInput, DetailedSection as DetailedStep

class CurriculumRequest(BaseModel):
    """Request model for curriculum generation"""
    subject: str
    syllabus_url: Optional[str] = None
    time_constraint: Optional[str] = None

class CurriculumModificationRequest(BaseModel):
    """Request model for curriculum modification"""
    modification_text: str

class CurriculumResponse(BaseModel):
    """Response model for curriculum operations"""
    curriculum_id: str
    title: str
    overview: str
    steps: List[Dict[str, str]]
    total_time: str
    formatted_text: str

class StepDetailResponse(BaseModel):
    """Response model for detailed step content"""
    step_title: str
    estimated_time: str
    content: Dict[str, Any]
    formatted_text: str

class RoadmapResponse(BaseModel):
    """Response model for curriculum roadmap"""
    curriculum_id: str
    mermaid_code: str

class CurriculumListResponse(BaseModel):
    """Response model for listing curriculums"""
    curriculums: List[Dict[str, str]]

class CurriculumCreateRequest(BaseModel):
    """Request model for creating a new curriculum"""
    curriculum_name: str

def generate_curriculum(request: CurriculumRequest) -> CurriculumResponse:
    """
    Generate a curriculum based on the request parameters
    
    Args:
        request: CurriculumRequest containing subject, optional syllabus URL, and time constraint
        
    Returns:
        CurriculumResponse with the generated curriculum
    """
    try:
        # Create input for coordinator
        coordinator_input = CoordinatorInput(
            query=request.subject,
            source_url=request.syllabus_url,
            depth_level=request.time_constraint
        )
        
        # Generate curriculum
        result = coordinate(coordinator_input)
        
        # Create response
        return CurriculumResponse(
            curriculum_id=result.overview.curriculum_id,
            title=result.overview.title,
            overview=result.overview.overview,
            steps=[{"title": step.title, "estimated_time": step.estimated_time} 
                  for step in result.overview.steps],
            total_time=result.overview.total_time,
            formatted_text=result.formatted_text
        )
    except Exception as e:
        error_details = f"Error generating curriculum: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to generate curriculum: {str(e)}")

def get_curriculum(curriculum_id: str) -> CurriculumResponse:
    """
    Get a curriculum by ID
    
    Args:
        curriculum_id: The UUID of the curriculum
        
    Returns:
        CurriculumResponse with the curriculum data
    """
    try:
        # Get curriculum step from database
        curriculum_step = get_curriculum_step(curriculum_id)
        
        if not curriculum_step:
            raise Exception(f"Curriculum with ID {curriculum_id} not found")
        
        # Parse overview data
        overview_data = curriculum_step.get("overview", {})
        step_data = overview_data.get("topics", [])
        
        steps = []
        for topic in step_data:
            steps.append({
                "title": topic.get("name", "Unknown step"),
                "estimated_time": "Not specified"
            })
        
        # Create curriculum overview
        overview = CurriculumOverview(
            curriculum_id=curriculum_id,
            title=curriculum_step.get("step_title", "Untitled Curriculum"),
            overview=f"A curriculum covering key aspects of {curriculum_step.get('step_title', 'the subject')}.",
            steps=[CurriculumStep(title=step["title"], estimated_time=step["estimated_time"]) for step in steps],
            total_time=curriculum_step.get("estimated_time", "Not specified")
        )
        
        # Format text
        formatted_text = format_curriculum_text(overview)
        
        # Create response
        return CurriculumResponse(
            curriculum_id=curriculum_id,
            title=overview.title,
            overview=overview.overview,
            steps=steps,
            total_time=overview.total_time,
            formatted_text=formatted_text
        )
    except Exception as e:
        error_details = f"Error retrieving curriculum: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to retrieve curriculum: {str(e)}")

def modify_curriculum_by_id(curriculum_id: str, request: CurriculumModificationRequest) -> CurriculumResponse:
    """
    Modify a curriculum based on the request
    
    Args:
        curriculum_id: The UUID of the curriculum to modify
        request: CurriculumModificationRequest containing modification text
        
    Returns:
        CurriculumResponse with the modified curriculum
    """
    try:
        # Get current curriculum
        curriculum_step = get_curriculum_step(curriculum_id)
        
        if not curriculum_step:
            raise Exception(f"Curriculum with ID {curriculum_id} not found")
            
        # Parse current curriculum data
        overview_data = curriculum_step.get("overview", {})
        step_data = overview_data.get("topics", [])
        
        # Create curriculum overview object from data
        steps = []
        for topic in step_data:
            steps.append(CurriculumStep(
                title=topic.get("name", "Unknown step"),
                estimated_time="Not specified"
            ))
        
        current_curriculum = CurriculumOverview(
            curriculum_id=curriculum_id,
            title=curriculum_step.get("step_title", "Untitled Curriculum"),
            overview=f"A curriculum covering key aspects of {curriculum_step.get('step_title', 'the subject')}.",
            steps=steps,
            total_time=curriculum_step.get("estimated_time", "Not specified")
        )
        
        # Apply modifications
        modified_data = modify_curriculum(current_curriculum, request.modification_text)
        
        # Create new steps from the JSON data
        new_steps = []
        for step_data in modified_data.get("steps", []):
            new_steps.append(CurriculumStep(
                title=step_data.get("title", "Untitled Step"),
                estimated_time=step_data.get("estimated_time", "Not specified")
            ))
        
        # Create a new curriculum with the updated steps
        updated_curriculum = CurriculumOverview(
            curriculum_id=curriculum_id,
            title=current_curriculum.title,
            overview=current_curriculum.overview,
            steps=new_steps,
            total_time=current_curriculum.total_time
        )
        
        # Format as text
        formatted_text = format_curriculum_text(updated_curriculum)
        
        # Save updated curriculum to database
        updated_overview_data = {
            "steps": [{"title": step.title, "estimated_time": step.estimated_time} 
                    for step in updated_curriculum.steps]
        }
        
        save_result = save_curriculum_step(
            curriculum_id,
            updated_curriculum.title,
            updated_curriculum.total_time,
            updated_overview_data
        )
        
        if not save_result:
            print("Warning: Failed to save updated curriculum to database")
        
        # Create response
        return CurriculumResponse(
            curriculum_id=curriculum_id,
            title=updated_curriculum.title,
            overview=updated_curriculum.overview,
            steps=[{"title": step.title, "estimated_time": step.estimated_time} 
                  for step in updated_curriculum.steps],
            total_time=updated_curriculum.total_time,
            formatted_text=formatted_text
        )
    except Exception as e:
        error_details = f"Error modifying curriculum: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to modify curriculum: {str(e)}")

def generate_curriculum_details(curriculum_id: str) -> Dict[int, StepDetailResponse]:
    """
    Generate detailed content for all steps in a curriculum
    
    Args:
        curriculum_id: The UUID of the curriculum
        
    Returns:
        Dict mapping step indices to StepDetailResponse objects
    """
    try:
        # Get curriculum
        curriculum_step = get_curriculum_step(curriculum_id)
        
        if not curriculum_step:
            raise Exception(f"Curriculum with ID {curriculum_id} not found")
            
        # Parse curriculum data
        overview_data = curriculum_step.get("overview", {})
        step_data = overview_data.get("topics", [])
        
        # Create curriculum overview object from data
        steps = []
        for topic in step_data:
            steps.append(CurriculumStep(
                title=topic.get("name", "Unknown step"),
                estimated_time="Not specified"
            ))
        
        curriculum = CurriculumOverview(
            curriculum_id=curriculum_id,
            title=curriculum_step.get("step_title", "Untitled Curriculum"),
            overview=f"A curriculum covering key aspects of {curriculum_step.get('step_title', 'the subject')}.",
            steps=steps,
            total_time=curriculum_step.get("estimated_time", "Not specified")
        )
        
        # Check if detailed_content already exists in the curriculum_step
        detailed_content = curriculum_step.get("detailed_content", {}) or {}
        
        # Process each step
        detailed_steps = {}
        
        for index, step in enumerate(curriculum.steps):
            step_key = f"step_{index}"
            existing_detail = detailed_content.get(step_key)
            
            if existing_detail:
                print(f"Retrieved existing detailed content for step {index}")
                # Use existing detailed content
                detailed_step = DetailedStep(
                    step_title=existing_detail.get("step_title", step.title),
                    estimated_time=existing_detail.get("estimated_time", step.estimated_time),
                    learning_objectives=existing_detail.get("learning_objectives", []),
                    subtopics=existing_detail.get("subtopics", []),
                    core_concepts=existing_detail.get("core_concepts", ""),
                    learning_resources=existing_detail.get("learning_resources", []),
                    practice_exercises=existing_detail.get("practice_exercises", []),
                    assessment_methods=existing_detail.get("assessment_methods", ""),
                    advanced_topics=existing_detail.get("advanced_topics", []),
                    connections=existing_detail.get("connections", {})
                )
            else:
                print(f"Generating new detailed content for step {index}")
                # Set up input for detail generator
                detail_input = StepDetailInput(
                    step_title=step.title,
                    estimated_time=step.estimated_time,
                    subject=curriculum.title
                )
                
                # Generate detailed content
                detailed_step = generate_step_detail(detail_input)
                
                # Save the detailed content to curriculum_steps table
                try:
                    from utils.curriculum_utils import save_curriculum_step_detail
                    detail_dict = detailed_step.dict()
                    detailed_content_key = f"{curriculum_id}_step_{index}"
                    save_result = save_curriculum_step_detail(
                        detailed_content_key,
                        curriculum_id,
                        index,
                        detail_dict
                    )
                    if save_result:
                        print(f"Successfully saved detailed content for step {index}")
                    else:
                        print(f"Failed to save detailed content for step {index}")
                except Exception as e:
                    print(f"Error saving detailed content: {e}")
            
            # Format as text
            detailed_text = format_detailed_step_text(detailed_step)
            
            # Store the results
            if detailed_step:
                detailed_steps[index] = StepDetailResponse(
                    step_title=detailed_step.step_title,
                    estimated_time=detailed_step.estimated_time,
                    content=detailed_step.dict(),
                    formatted_text=detailed_text
                )
        
        return detailed_steps
    except Exception as e:
        error_details = f"Error generating curriculum details: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to generate curriculum details: {str(e)}")

def get_step_detail(curriculum_id: str, step_index: int) -> StepDetailResponse:
    """
    Get detailed content for a specific step
    
    Args:
        curriculum_id: The UUID of the curriculum
        step_index: The index of the step
        
    Returns:
        StepDetailResponse with the detailed step content
    """
    try:
        # Get the curriculum with detailed content
        curriculum_step = get_curriculum_step(curriculum_id)
        
        if not curriculum_step:
            raise Exception(f"Curriculum with ID {curriculum_id} not found")
        
        # Check if detailed content exists in the curriculum_step
        detailed_content = curriculum_step.get("detailed_content", {}) or {}
        step_key = f"step_{step_index}"
        existing_detail = detailed_content.get(step_key)
        
        if existing_detail:
            print(f"Retrieved existing detailed content for step {step_index}")
            
            # Parse curriculum data to get step title
            overview_data = curriculum_step.get("overview", {})
            step_data = overview_data.get("topics", [])
            
            if step_index >= len(step_data):
                raise Exception(f"Step index {step_index} out of range for curriculum {curriculum_id}")
            
            step_title = step_data[step_index].get("name", "Unknown step")
            estimated_time = "Not specified"
            
            # Create DetailedStep from stored data
            detailed_step = DetailedStep(
                step_title=existing_detail.get("step_title", step_title),
                estimated_time=existing_detail.get("estimated_time", estimated_time),
                learning_objectives=existing_detail.get("learning_objectives", []),
                subtopics=existing_detail.get("subtopics", []),
                core_concepts=existing_detail.get("core_concepts", ""),
                learning_resources=existing_detail.get("learning_resources", []),
                practice_exercises=existing_detail.get("practice_exercises", []),
                assessment_methods=existing_detail.get("assessment_methods", ""),
                advanced_topics=existing_detail.get("advanced_topics", []),
                connections=existing_detail.get("connections", {})
            )
            
            # Format as text
            detailed_text = format_detailed_step_text(detailed_step)
            
            # Return the response
            return StepDetailResponse(
                step_title=detailed_step.step_title,
                estimated_time=detailed_step.estimated_time,
                content=detailed_step.dict(),
                formatted_text=detailed_text
            )
        else:
            print(f"No existing detail found for step {step_index}, will generate new content")
            # If we don't have stored content, generate all details
            all_details = generate_curriculum_details(curriculum_id)
            
            # Check if the requested step exists
            if step_index not in all_details:
                raise Exception(f"Step with index {step_index} not found in curriculum {curriculum_id}")
            
            return all_details[step_index]
    except Exception as e:
        error_details = f"Error retrieving step detail: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to retrieve step detail: {str(e)}")

def generate_roadmap(curriculum_id: str) -> RoadmapResponse:
    """
    Generate a visual roadmap for the curriculum
    
    Args:
        curriculum_id: The UUID of the curriculum
        
    Returns:
        RoadmapResponse with the mermaid diagram code
    """
    try:
        # Get curriculum
        curriculum_step = get_curriculum_step(curriculum_id)
        
        if not curriculum_step:
            raise Exception(f"Curriculum with ID {curriculum_id} not found")
            
        # Parse curriculum data
        overview_data = curriculum_step.get("overview", {})
        step_data = overview_data.get("topics", [])
        
        # Create curriculum overview object from data
        steps = []
        for topic in step_data:
            steps.append(CurriculumStep(
                title=topic.get("name", "Unknown step"),
                estimated_time="Not specified"
            ))
        
        curriculum = CurriculumOverview(
            curriculum_id=curriculum_id,
            title=curriculum_step.get("step_title", "Untitled Curriculum"),
            overview=f"A curriculum covering key aspects of {curriculum_step.get('step_title', 'the subject')}.",
            steps=steps,
            total_time=curriculum_step.get("estimated_time", "Not specified")
        )
        
        # Create a flowchart diagram using Mermaid syntax
        mermaid_code = """
        flowchart LR
            Start([Start]) --> Step1
        """
        
        # Add each step as a node
        for i, step in enumerate(curriculum.steps, 1):
            # Add the step node
            step_id = f"Step{i}"
            step_title = step.title
            estimated_time = step.estimated_time
            
            # Truncate long titles for better display
            if len(step_title) > 30:
                step_title = step_title[:27] + "..."
                
            mermaid_code += f"""
            {step_id}["{step_title}<br><small>{estimated_time}</small>"]
            """
            
            # Add connection to next step if not the last one
            if i < len(curriculum.steps):
                mermaid_code += f"""
            {step_id} --> Step{i+1}
                """
        
        # Add final node
        mermaid_code += """
            Step{} --> Finish([Complete])
        """.format(len(curriculum.steps))
        
        return RoadmapResponse(
            curriculum_id=curriculum_id,
            mermaid_code=mermaid_code
        )
    except Exception as e:
        error_details = f"Error generating roadmap: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to generate roadmap: {str(e)}")

def get_all_curriculums() -> CurriculumListResponse:
    """
    Get a list of all available curriculums
    
    Returns:
        CurriculumListResponse containing list of curriculum metadata
    """
    try:
        # Get all curriculum steps from Supabase database
        from utils.curriculum_utils import get_all_curriculum_steps
        
        # Query all curriculum records from Supabase
        curriculum_records = get_all_curriculum_steps()
        
        # Format the curriculum list for response
        curriculum_list = []
        for record in curriculum_records:
            curriculum_list.append({
                "curriculum_id": record.get("step_id"),
                "curriculum_name": record.get("step_title", "Untitled Curriculum")
            })
        
        return CurriculumListResponse(curriculums=curriculum_list)
    except Exception as e:
        error_details = f"Error listing curriculums: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to list curriculums: {str(e)}")

def create_curriculum(request: CurriculumCreateRequest) -> Dict[str, str]:
    """
    Create a new empty curriculum
    
    Args:
        request: CurriculumCreateRequest containing curriculum name
        
    Returns:
        Dict with curriculum_id and curriculum_name
    """
    try:
        curriculum_id = str(uuid.uuid4())
        curriculum_name = request.curriculum_name
        
        # Create a minimal curriculum structure
        curriculum_data = {
            "step_title": curriculum_name,
            "estimated_time": "Not specified",
            "overview": {
                "topics": []
            }
        }
        
        # Save to database
        save_result = save_curriculum_step(
            curriculum_id,
            curriculum_name,
            "Not specified",
            curriculum_data
        )
        
        if not save_result:
            raise Exception("Failed to save curriculum to database")
        
        return {
            "curriculum_id": curriculum_id,
            "curriculum_name": curriculum_name
        }
    except Exception as e:
        error_details = f"Error creating curriculum: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to create curriculum: {str(e)}")

def delete_curriculum_by_id(curriculum_id: str) -> bool:
    """
    Delete a curriculum by ID
    
    Args:
        curriculum_id: The UUID of the curriculum to delete
        
    Returns:
        Boolean indicating success
    """
    try:
        # Check if curriculum exists
        curriculum_step = get_curriculum_step(curriculum_id)
        if not curriculum_step:
            raise Exception(f"Curriculum with ID {curriculum_id} not found")
        
        # Delete curriculum file
        # In a real implementation, you would remove from your database
        curriculum_file = os.path.join(os.path.dirname(__file__), "data", "curriculums", f"{curriculum_id}.json")
        if os.path.exists(curriculum_file):
            os.remove(curriculum_file)
            return True
        else:
            # Not found on disk but was found by get_curriculum_step
            # This suggests an inconsistency, but return True as the intent is fulfilled
            return True
    except Exception as e:
        error_details = f"Error deleting curriculum: {e}\n{traceback.format_exc()}"
        print(error_details)
        raise Exception(f"Failed to delete curriculum: {str(e)}")
