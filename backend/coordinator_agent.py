import os
import json
import uuid
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

# Import document processing and search functionalities
from document_loader import process_web, process_pdf
from search import google_search
# Import Supabase client
from utils.supabase_client import initialize_supabase
# Import overview agent
from agents.overview_agent import generate_overview, format_curriculum_text, format_any_overview_text, CurriculumOverview

class ResearchInput(BaseModel):
    """Input structure for the knowledge coordinator agent"""
    query: str
    source_url: Optional[str] = None
    depth_level: Optional[str] = None

class KnowledgeOutput(BaseModel):
    """Output structure from the knowledge coordinator agent"""
    research_id: str  # UUID for this research
    topic: str
    summary: str
    source_materials: List[Dict[str, str]] = Field(default_factory=list)
    key_concepts: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_structure: Dict[str, Any] = Field(default_factory=dict)
    depth_metrics: Dict[str, str] = Field(default_factory=dict)
    complexity_level: str = ""

class ResearchCompleteOutput(BaseModel):
    """Complete output including both raw data and formatted overview"""
    raw_data: KnowledgeOutput
    overview: Dict[str, Any]  # General knowledge overview
    formatted_text: str

def save_curriculum_step(step_id: str, step_title: str, estimated_time: str, overview=None, detailed_content=None):
    """
    Save curriculum step to Supabase
    
    Args:
        step_id: UUID for the curriculum step
        step_title: Title of the curriculum step (subject)
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

def get_default_ml_topics():
    """Fallback function to provide default ML curriculum topics when API is unavailable."""
    return [
        {
            "name": "Introduction to Machine Learning",
            "key_concepts": ["Supervised Learning", "Unsupervised Learning", "Reinforcement Learning"],
            "skills": ["Basic Python", "Understanding ML Terminology"],
            "prerequisites": []
        },
        {
            "name": "Data Preprocessing",
            "key_concepts": ["Feature Scaling", "Missing Values", "Categorical Encoding"],
            "skills": ["Data Cleaning", "Feature Engineering"],
            "prerequisites": ["Introduction to Machine Learning"]
        },
        {
            "name": "Regression Algorithms",
            "key_concepts": ["Linear Regression", "Polynomial Regression", "Regularization"],
            "skills": ["Model Evaluation", "Hyperparameter Tuning"],
            "prerequisites": ["Data Preprocessing"]
        },
        {
            "name": "Classification Algorithms",
            "key_concepts": ["Logistic Regression", "Decision Trees", "Random Forest"],
            "skills": ["Confusion Matrix", "Classification Metrics"],
            "prerequisites": ["Data Preprocessing"]
        },
        {
            "name": "Clustering Algorithms",
            "key_concepts": ["K-Means", "Hierarchical Clustering", "DBSCAN"],
            "skills": ["Cluster Analysis", "Dimensionality Reduction"],
            "prerequisites": ["Data Preprocessing"]
        }
    ]

def coordinate(user_input: ResearchInput) -> ResearchCompleteOutput:
    """
    Coordinates processing of user input to create structured data for curriculum planning.
    
    This function:
    1. Processes syllabus if provided
    2. Uses Google search for additional information if needed
    3. Extracts key topics and concepts
    4. Structures the data for curriculum overview generation
    5. Generates a formatted curriculum overview using the overview agent
    
    Args:
        user_input: Structure containing query, optional syllabus URL, and time constraint
        
    Returns:
        ResearchCompleteOutput: Complete output with raw data and formatted overview
    """
    # Generate UUID for this curriculum step
    research_id = str(uuid.uuid4())
    
    # Extract inputs
    query = user_input.query
    source_url = user_input.source_url
    depth_level = user_input.depth_level
    
    # Initialize output structure with UUID
    output = KnowledgeOutput(
        research_id=research_id,
        topic=query,
        summary=f"Research on {query}",
        source_materials=[],
        key_concepts=[],
        knowledge_structure={},
        depth_metrics={},
        complexity_level=""
    )
    
    # Step 1: Process syllabus if provided
    extracted_content = []
    if source_url:
        print(f"Processing source from: {source_url}")
        
        # Determine if it's a web page or file to download
        if source_url.endswith('.pdf'):
            # Handle PDF syllabus
            try:
                # Download the PDF
                response = requests.get(source_url, stream=True)
                response.raise_for_status()
                
                # Save to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        tmp_file.write(chunk)
                    temp_path = tmp_file.name
                
                # Process the PDF
                documents = process_pdf(temp_path)
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
                # Extract content
                for doc in documents:
                    extracted_content.append(doc.page_content)
                    
                # Add to source materials
                output.source_materials.append({
                    "type": "pdf",
                    "url": source_url,
                    "title": source_url.split("/")[-1]
                })
                
            except Exception as e:
                print(f"Error processing PDF source: {e}")
        else:
            # Process as web URL
            try:
                documents = process_web(source_url)
                
                # Extract content
                for doc in documents:
                    extracted_content.append(doc.page_content)
                
                # Add to source materials
                output.source_materials.append({
                    "type": "web",
                    "url": source_url,
                    "title": source_url
                })
                
            except Exception as e:
                print(f"Error processing web source: {e}")
    
    # Step 2: If no source provided or extraction failed, use Google search
    if not extracted_content:
        print("No source provided or extraction failed, using Google search")
        search_query = f"{query} research source"
        try:
            search_results, search_links = google_search(search_query)
            
            if search_results:
                extracted_content.append(search_results)
                
                # Add search links to source materials
                for link in search_links:
                    output.source_materials.append({
                        "type": "web",
                        "url": link,
                        "title": link
                    })
                
                # Always ensure we have extracted content from Google search
                # to generate topics even without a source
                print("Using search results to extract research topics")
        except Exception as e:
            print(f"Error performing Google search: {e}")
    
    # Step 3: Extract key topics and concepts from content
    if extracted_content:
        combined_content = "\n\n".join(extracted_content)
        
        # Use direct Gemini API to extract topics
        from google import genai
        
        try:
            api_key = os.getenv("GEMINI_API_KEY", "")
            client = genai.Client(api_key=api_key)
            
            extract_prompt = f"""
            Based on the following content about '{query}', extract:
            
            1. The main topics that should be included in a research
            2. Key concepts and skills for each topic
            3. Logical ordering of topics
            4. Any prerequisites or dependent relationships between topics
            
            Content:
            {combined_content[:10000]}  # Limit content length to avoid token limits
            
            Format your response as JSON with this structure:
            {{
              "topics": [
                {{
                  "name": "Topic name",
                  "key_concepts": ["concept1", "concept2"],
                  "skills": ["skill1", "skill2"],
                  "prerequisites": ["prerequisite topics if any"]
                }}
              ]
            }}
            """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=extract_prompt,
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
            extracted_data = json.loads(response_text.strip())
            
            if "topics" in extracted_data:
                output.key_concepts = extracted_data["topics"]
        
        except Exception as e:
            print(f"Error extracting topics: {e}")
            # Fallback to default topics if API call fails
            print("Using default ML topics as fallback")
            if "machine learning" in query.lower():
                output.key_concepts = get_default_ml_topics()
            else:
                # Generate simple generic topics based on the query
                output.key_concepts = [
                    {
                        "name": f"Introduction to {query}",
                        "key_concepts": ["Basic concepts", "Terminology", "History"],
                        "skills": ["Fundamental understanding"],
                        "prerequisites": []
                    },
                    {
                        "name": f"Core {query} Techniques",
                        "key_concepts": ["Key principles", "Standard methods"],
                        "skills": ["Application of concepts"],
                        "prerequisites": [f"Introduction to {query}"]
                    },
                    {
                        "name": f"Advanced {query}",
                        "key_concepts": ["Complex techniques", "Current research"],
                        "skills": ["Problem solving", "Critical analysis"],
                        "prerequisites": [f"Core {query} Techniques"]
                    }
                ]
    else:
        # If we have no extracted content, use default topics
        print("No content extracted, using default topic structure")
        if "machine learning" in query.lower():
            output.key_concepts = get_default_ml_topics()
        else:
            # Generate simple generic topics based on the query
            output.key_concepts = [
                {
                    "name": f"Introduction to {query}",
                    "key_concepts": ["Basic concepts", "Terminology", "History"],
                    "skills": ["Fundamental understanding"],
                    "prerequisites": []
                },
                {
                    "name": f"Core {query} Techniques",
                    "key_concepts": ["Key principles", "Standard methods"],
                    "skills": ["Application of concepts"],
                    "prerequisites": [f"Introduction to {query}"]
                },
                {
                    "name": f"Advanced {query}",
                    "key_concepts": ["Complex techniques", "Current research"],
                    "skills": ["Problem solving", "Critical analysis"],
                    "prerequisites": [f"Core {query} Techniques"]
                }
            ]
    
    # Step 4: Create suggested structure based on topics and time constraint
    if output.key_concepts:
        try:
            # Use direct Gemini API to create structure
            api_key = os.getenv("GEMINI_API_KEY", "")
            client = genai.Client(api_key=api_key)
            
            structure_prompt = f"""
            Create a knowledge structure for '{query}' based on these topics:
            
            {json.dumps(output.key_concepts)}
            
            {"Depth level: " + depth_level if depth_level else "No specific depth level provided."}
            
            Format your response as JSON with this structure:
            {{
              "knowledge_path": [
                {{
                  "module": "Module name",
                  "topics": ["Topic 1", "Topic 2"],
                  "learning_outcomes": ["outcome1", "outcome2"],
                  "suggested_duration": "X weeks/hours"
                }}
              ],
              "depth_metrics": {{
                "module1": "duration",
                "module2": "duration"
              }}
            }}
            """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=structure_prompt,
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
            structure_data = json.loads(response_text.strip())
            
            if "knowledge_path" in structure_data:
                output.knowledge_structure = {
                    "knowledge_path": structure_data["knowledge_path"]
                }
                
            if "depth_metrics" in structure_data:
                output.depth_metrics = structure_data["depth_metrics"]
                
            # Set total time directly from time constraint
            if depth_level:
                output.complexity_level = depth_level
            else:
                output.complexity_level = "Not specified"
        
        except Exception as e:
            print(f"Error creating knowledge structure: {e}")
            # Set default time if structure creation failed
            output.complexity_level = depth_level if depth_level else "8 weeks (default)"
    else:
        # No topics, set default time
        output.complexity_level = depth_level if depth_level else "Not specified"
    
    # Save curriculum step to Supabase
    overview_data = {
        "topics": output.key_concepts,
        # Removed source_materials from what gets stored
    }
    
    detailed_content = {
        "knowledge_path": output.knowledge_structure.get("knowledge_path", []),
        "depth_metrics": output.depth_metrics
    }
    
    # Save to Supabase
    save_result = save_curriculum_step(
        research_id,
        query,  # subject as step_title
        output.complexity_level,  # total_time as estimated_time
        overview_data,
        detailed_content
    )
    
    if not save_result:
        print("Warning: Failed to save curriculum step to database")
    
    # Step 5: Generate curriculum overview using the overview agent
    print("Generating detailed curriculum overview...")
    try:
        # Clear source materials before passing to overview generation
        output.source_materials = []
        
        overview_result = generate_overview(output)
        
        # Format as text - use the new universal formatter
        formatted_text = format_any_overview_text(overview_result)
        print("Curriculum overview generation complete!")
        
        # IMPORTANT: Do not perform automatic additional searches for knowledge context here
        # Let the user confirm the overview structure first before generating detailed content
    except Exception as e:
        print(f"Error generating overview: {e}")
        # Create a minimal overview if generation failed
        from agents.overview_agent import CurriculumStep, CurriculumOverview
        overview_result = CurriculumOverview(
            curriculum_id=research_id,
            title=f"Research on {query}",
            overview=f"A comprehensive research covering the key aspects of {query}.",
            steps=[
                CurriculumStep(
                    title=f"Introduction to {query}",
                    objectives=["Understand basic concepts", "Learn terminology", "Explore applications"],
                    estimated_time="2 weeks"
                )
            ],
            total_time=output.complexity_level
        )
        formatted_text = format_curriculum_text(overview_result)
    
    # Convert the overview_result object to a dictionary
    # Only convert if it's not already a dictionary
    if isinstance(overview_result, dict):
        overview_dict = overview_result
    else:
        overview_dict = overview_result.dict() if hasattr(overview_result, 'dict') else vars(overview_result)
    
    # Return complete output
    return ResearchCompleteOutput(
        raw_data=output,
        overview=overview_dict,
        formatted_text=formatted_text
    )

if __name__ == "__main__":
    # Example usage
    test_input = ResearchInput(
        query="Introduction to Machine Learning",
        depth_level="8 weeks"
    )
    
    result = coordinate(test_input)
