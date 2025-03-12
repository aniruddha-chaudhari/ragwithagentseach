from google import genai
from typing import Generator
import logging

logger = logging.getLogger(__name__)

def prepare_document(file_path: str, initial_prompt: str) -> Generator[str, None, None]:
    """
    Prepares the document and gets initial response with streaming using the provided prompt.
    Returns: Generator yielding response chunks
    """
    try:
        # Initialize the Google AI client
        client = genai.Client(api_key="AIzaSyD4lR1WQ1yaZumSFtMVTG_0Y8d0oRy1XhA")
        
        # Upload the file
        uploaded_file = client.files.upload(file=file_path)
        logger.info("File uploaded successfully to AI service")
        
        # Enhanced prompt for image description
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            logger.info("Processing image file")
            initial_prompt = """
            Please describe this image in detail. Include:
            1. Main subject/content
            2. Visual style and composition
            3. Colors and notable features
            4. Overall impression and purpose
            5. Any text or symbols if present
            
            Format the response in clear sections.
            """
        
        # Use the provided initial prompt for other file types
        response_stream = client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=[uploaded_file, initial_prompt]
        )
        
        full_response = ""
        for chunk in response_stream:
            if chunk.text:
                full_response += chunk.text
                yield chunk.text
        logger.info("Document analysis completed")
        logger.debug(f"Full response: {full_response}")
        
    except Exception as e:
        error_msg = f"Error preparing document: {str(e)}"
        logger.error(error_msg, exc_info=True)
        yield error_msg