import uuid
from typing import Dict, Any, Optional, Tuple, List
from utils.supabase_client import initialize_supabase

def create_curriculum_step(step_title: str, estimated_time: str, overview=None, detailed_content=None) -> Tuple[str, bool]:
    """
    Create a new curriculum step and save to Supabase
    
    Args:
        step_title: Title of the curriculum step
        estimated_time: Estimated time for completion
        overview: JSON data for overview (optional)
        detailed_content: JSON data for detailed content (optional)
        
    Returns:
        Tuple[str, bool]: (step_id, success)
    """
    step_id = str(uuid.uuid4())
    success = save_curriculum_step(step_id, step_title, estimated_time, overview, detailed_content)
    return step_id, success

def save_curriculum_step(step_id: str, step_title: str, estimated_time: str, overview=None, detailed_content=None) -> bool:
    """
    Save curriculum step to Supabase
    
    Args:
        step_id: UUID for the curriculum step
        step_title: Title of the curriculum step
        estimated_time: Estimated time for completion
        overview: JSON data for overview (optional)
        detailed_content: JSON data for detailed content (optional)
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        # Initialize Supabase client
        supabase = initialize_supabase()
        if not supabase:
            print("Failed to initialize Supabase client")
            return False
            
        # Prepare data
        data = {
            "step_id": step_id,
            "step_title": step_title,
            "estimated_time": estimated_time
        }
        
        # Add JSON data if provided
        if overview:
            data["overview"] = overview
            
        if detailed_content:
            data["detailed_content"] = detailed_content
            
        # Insert data into Supabase
        response = supabase.table("curriculum_steps").insert(data).execute()
        print(f"Successfully saved curriculum step with ID: {step_id}")
        return True
        
    except Exception as e:
        print(f"Error saving curriculum step to Supabase: {e}")
        return False

def get_curriculum_step(step_id: str) -> Optional[Dict[str, Any]]:
    """
    Get curriculum step from Supabase
    
    Args:
        step_id: UUID of the curriculum step
        
    Returns:
        Optional[Dict[str, Any]]: Curriculum step data or None if not found
    """
    try:
        # Initialize Supabase client
        supabase = initialize_supabase()
        if not supabase:
            print("Failed to initialize Supabase client")
            return None
            
        # Query Supabase
        response = supabase.table("curriculum_steps").select("*").eq("step_id", step_id).execute()
        
        if response and response.data and len(response.data) > 0:
            return response.data[0]
            
        return None
        
    except Exception as e:
        print(f"Error getting curriculum step from Supabase: {e}")
        return None

def get_all_curriculum_steps() -> List[Dict[str, Any]]:
    """
    Get all curriculum steps from Supabase
    
    Returns:
        List[Dict[str, Any]]: List of curriculum step data
    """
    try:
        # Initialize Supabase client
        supabase = initialize_supabase()
        if not supabase:
            print("Failed to initialize Supabase client")
            return []
            
        # Query Supabase
        response = supabase.table("curriculum_steps").select("*").execute()
        
        if response and response.data:
            return response.data
            
        return []
        
    except Exception as e:
        print(f"Error getting curriculum steps from Supabase: {e}")
        return []

def update_curriculum_step(step_id: str, step_title: str, estimated_time: str, overview=None, detailed_content=None) -> bool:
    """
    Update an existing curriculum step in Supabase
    
    Args:
        step_id: UUID for the curriculum step
        step_title: Title of the curriculum step
        estimated_time: Estimated time for completion
        overview: JSON data for overview (optional)
        detailed_content: JSON data for detailed content (optional)
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        # Initialize Supabase client
        supabase = initialize_supabase()
        if not supabase:
            print("Failed to initialize Supabase client")
            return False
            
        # Prepare data
        data = {
            "step_title": step_title,
            "estimated_time": estimated_time
        }
        
        # Add JSON data if provided
        if overview:
            data["overview"] = overview
            
        if detailed_content:
            data["detailed_content"] = detailed_content
            
        # Update data in Supabase
        response = supabase.table("curriculum_steps").update(data).eq("step_id", step_id).execute()
        print(f"Successfully updated curriculum step with ID: {step_id}")
        return True
        
    except Exception as e:
        print(f"Error updating curriculum step in Supabase: {e}")
        return False

def save_curriculum_step_detail(detail_id: str, curriculum_id: str, step_index: int, detail_data: Dict[str, Any]) -> bool:
    """
    Save detailed curriculum step content to the detailed_content column of curriculum_steps
    
    Args:
        detail_id: Unique identifier for the detailed step content (not used directly)
        curriculum_id: The curriculum ID this detail belongs to
        step_index: The index of the step within the curriculum
        detail_data: The detailed step content data
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        # Initialize Supabase client
        supabase = initialize_supabase()
        if not supabase:
            print("Failed to initialize Supabase client")
            return False
        
        # First, get the current detailed_content if it exists
        response = supabase.table("curriculum_steps").select("detailed_content").eq("step_id", curriculum_id).execute()
        
        if not response or not response.data or len(response.data) == 0:
            print(f"Curriculum with ID {curriculum_id} not found")
            return False
        
        # Extract current detailed_content, or create a new object if it doesn't exist
        current_detailed_content = response.data[0].get("detailed_content", {}) or {}
        
        # Add the new step detail into the detailed_content object
        # Use a string key for step index to ensure consistent JSON format
        step_key = f"step_{step_index}"
        current_detailed_content[step_key] = detail_data
        
        # Update the curriculum_steps table with the new detailed_content
        update_data = {
            "detailed_content": current_detailed_content
        }
        
        update_response = supabase.table("curriculum_steps").update(update_data).eq("step_id", curriculum_id).execute()
        
        print(f"Successfully saved detailed content for curriculum {curriculum_id}, step {step_index}")
        return True
        
    except Exception as e:
        print(f"Error saving curriculum step detail to Supabase: {e}")
        return False

def get_curriculum_step_detail(detail_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed curriculum step content from the detailed_content column
    
    Args:
        detail_id: String in format "{curriculum_id}_step_{step_index}"
        
    Returns:
        Optional[Dict[str, Any]]: Detailed step content data or None if not found
    """
    try:
        # Initialize Supabase client
        supabase = initialize_supabase()
        if not supabase:
            print("Failed to initialize Supabase client")
            return None
        
        # Parse the detail_id to extract curriculum_id and step_index
        parts = detail_id.split("_step_")
        if len(parts) != 2:
            print(f"Invalid detail_id format: {detail_id}")
            return None
            
        curriculum_id = parts[0]
        step_index = parts[1]
        
        # Get the curriculum step from Supabase
        response = supabase.table("curriculum_steps").select("detailed_content").eq("step_id", curriculum_id).execute()
        
        if not response or not response.data or len(response.data) == 0:
            print(f"Curriculum with ID {curriculum_id} not found")
            return None
            
        # Extract the detailed_content
        detailed_content = response.data[0].get("detailed_content", {}) or {}
        
        # Get the specific step data
        step_key = f"step_{step_index}"
        step_data = detailed_content.get(step_key)
        
        if not step_data:
            print(f"No detailed content found for step {step_index} in curriculum {curriculum_id}")
            return None
            
        return step_data
        
    except Exception as e:
        print(f"Error getting curriculum step detail from Supabase: {e}")
        return None
