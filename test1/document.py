import json
import logging
from google import genai
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Tuple, TypedDict, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PaperCheckResult(BaseModel):
    Name: str = Field("", description="Paper taker's name or anything that hels identify the paper taker")
    marks: int
    remarks: List[str]
    suggestions: List[str]
    errors: List[str]

class ProcessResult(TypedDict):
    success: bool
    error: str | None
    results: List[Dict[str, Any]] | None

def prepare_document(file_path: str) -> Dict[str, Any]:
    """
    Prepares the document and gets initial response
    Returns: Dictionary with raw response
    """
    try:
        logger.info(f"Starting document preparation for file: {file_path}")
        # Initialize the Google AI client
        client = genai.Client(api_key="AIzaSyD4lR1WQ1yaZumSFtMVTG_0Y8d0oRy1XhA")
        
        # Upload the file
        uploaded_file = client.files.upload(file=file_path)
        logger.info("File uploaded successfully")
        
        # First prompt for general analysis
        initial_prompt = """
        Analyze this academic paper and provide feedback. Include:
        1. Overall quality score (0-100)
        2. Positive aspects of the paper
        3. Areas that need improvement
        4. Any errors or problems found
        """
        
        # Get initial response
        initial_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[uploaded_file, initial_prompt]
        )
        logger.info("Received initial AI response")
        logger.debug(f"Initial response: {initial_response.text}")
        
        return {
            "success": True, 
            "uploaded_file": uploaded_file,
            "initial_response": initial_response.text
        }
        
    except Exception as e:
        logger.error(f"Error in prepare_document: {str(e)}", exc_info=True)
        return {"success": False, "error": f"Error preparing document: {str(e)}"}

def analyze_document(initial_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes initial response and converts it to structured format
    Returns: Dictionary with structured results
    """
    try:
        if not initial_result["success"]:
            logger.warning("Initial result was not successful")
            return initial_result
            
        logger.info("Starting document analysis")
        client = genai.Client(api_key="AIzaSyD4lR1WQ1yaZumSFtMVTG_0Y8d0oRy1XhA")
        
        # Updated structure prompt to allow roll no. or name in the "Name" field
        structure_prompt = f"""
        Convert the following feedback into a structured JSON format:

        {initial_result['initial_response']}

        The JSON should have this structure:
        {{  "Name": "Roll No or name of the paper taker if found, otherwise null",
            "marks": integer (0-100) it should depend on how good remarks are and how many errors there are,
            "remarks": [list of positive comments],
            "suggestions": [list of improvement areas],
            "errors": [list of problems found]
        }}

        IMPORTANT: Ensure marks is a valid integer between 0 and 100. If no specific score is found, use 0.
        Ensure all arrays are empty lists [] instead of null when there are no items.
        """
        
        # Get structured response
        structured_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=structure_prompt,
            config={
                'response_mime_type': 'application/json'
            }
        )
        
        logger.info("Received structured response from AI")
        logger.debug(f"Structured response: {structured_response.text}")
        
        # Parse the response safely
        try:
            # Clean the response text to ensure it's valid JSON
            response_text = structured_response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
            logger.info("Successfully parsed JSON response")
            
            # Ensure data structure is correct and marks is an integer
            if isinstance(data, dict):
                data["marks"] = int(data.get("marks", 0))  # Convert to int, default to 0
                data["Name"] = data.get("Name") or ""
                data["remarks"] = data.get("remarks") or []
                data["suggestions"] = data.get("suggestions") or []
                data["errors"] = data.get("errors") or []
                logger.info(f"Processed data structure: marks={data['marks']}, remarks={len(data['remarks'])}, suggestions={len(data['suggestions'])}, errors={len(data['errors'])}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Failed to parse AI response: {str(e)}"}
        except (ValueError, TypeError) as e:
            logger.error(f"Value error in marks: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Invalid marks value: {str(e)}"}
        
        if not isinstance(data, list):
            data = [data]
            
        results = [PaperCheckResult(**item) for item in data]
        final_results = {"success": True, "results": [r.model_dump() for r in results]}
        logger.info("Successfully created final response")
        logger.debug(f"Final response: {final_results}")
        return final_results
        
    except Exception as e:
        logger.error(f"Error in analyze_document: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

def process_document(file_path: str) -> ProcessResult:
    """
    Main function that coordinates the document processing
    """
    try:
        logger.info(f"Starting document processing for file: {file_path}")
        # First get raw analysis
        initial_result = prepare_document(file_path)
        if not initial_result["success"]:
            logger.error(f"Document preparation failed: {initial_result['error']}")
            return {"success": False, "error": initial_result["error"], "results": None}
            
        # Then convert to structured format
        result = analyze_document(initial_result)
        if not result["success"]:
            logger.error(f"Document analysis failed: {result['error']}")
            return {"success": False, "error": result["error"], "results": None}
            
        logger.info("Document processing completed successfully")
        logger.debug(f"Final process result: {result}")
        return {"success": True, "error": None, "results": result["results"]}
        
    except Exception as e:
        logger.error(f"Error in process_document: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e), "results": None}

if __name__ == "__main__":
    file_path = 'spcc3.pdf'
    result = process_document(file_path)
    
    if result["success"]:
        for paper_result in result["results"]:
            print(f"Name: {paper_result['Name']}")
            print(f"Marks: {paper_result['marks']}")
            print(f"Remarks: {paper_result['remarks']}")
            print(f"Suggestions: {paper_result['suggestions']}")
            print(f"Errors: {paper_result['errors']}")
            print("-" * 50)
    else:
        print("Error:", result["error"])