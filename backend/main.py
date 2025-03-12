import os
import json
import tempfile
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager
import google.generativeai as genai

# Import shared functionality from embedder.py
from embedder import (
    init_pinecone,
    create_vector_store,
    check_document_relevance,
)

from search import google_search

# Import document processing functions
from document_loader import prepare_document, process_pdf, process_web, process_image

# Import agents
from agents.writeragents import get_query_rewriter_agent, get_rag_agent, test_url_detector

# Load environment variables
load_dotenv()

# Get API keys from environment variables with fallbacks
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")

# Hardcoded similarity threshold
SIMILARITY_THRESHOLD = 0.7

# Initialize app state
app_state = {
    "vector_store": None,
    "processed_documents": [],
    "pinecone_client": None
}

# Setup lifespan for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize on startup
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    genai.configure(api_key=GOOGLE_API_KEY)
    app_state["pinecone_client"] = init_pinecone(PINECONE_API_KEY)
    
    yield
    
    # Clean up on shutdown
    app_state["vector_store"] = None
    app_state["processed_documents"] = []

app = FastAPI(title="Teacher Assistant API", description="API for teacher assistant with RAG capabilities", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for requests and responses
class MessageRequest(BaseModel):
    content: str
    force_web_search: bool = False

class MessageResponse(BaseModel):
    content: str
    sources: List[Dict[str, str]] = []

class ProcessUrlRequest(BaseModel):
    url: HttpUrl

class SourceResponse(BaseModel):
    sources: List[str]

# API routes
@app.get("/")
async def root():
    return {"message": "Teacher Assistant API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "google_api_key": bool(GOOGLE_API_KEY),
        "pinecone_api_key": bool(PINECONE_API_KEY),
        "pinecone_client": bool(app_state["pinecone_client"]),
        "documents_processed": len(app_state["processed_documents"])
    }

@app.post("/process/document", response_model=SourceResponse)
async def process_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Process a document and add to vector store"""
    file_name = file.filename
    if file_name in app_state["processed_documents"]:
        return {"sources": app_state["processed_documents"]}
    
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        
        # Process based on file type
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            with open(temp_path, 'rb') as f:
                texts = process_image(f)
            doc_type = "Image"
        else:  # PDF or other document types
            with open(temp_path, 'rb') as f:
                texts = process_pdf(f)
            doc_type = "Document"
            
        # Clean up temp file
        os.unlink(temp_path)
        
        if texts and app_state["pinecone_client"]:
            if app_state["vector_store"]:
                app_state["vector_store"].add_documents(texts)
            else:
                app_state["vector_store"] = create_vector_store(app_state["pinecone_client"], texts)
            app_state["processed_documents"].append(file_name)
            
        return {"sources": app_state["processed_documents"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/process/url", response_model=SourceResponse)
async def process_url(request: ProcessUrlRequest):
    """Process a URL and add to vector store"""
    web_url = str(request.url)
    if web_url in app_state["processed_documents"]:
        return {"sources": app_state["processed_documents"]}
    
    try:
        texts = process_web(web_url)
        if texts and app_state["pinecone_client"]:
            if app_state["vector_store"]:
                app_state["vector_store"].add_documents(texts)
            else:
                app_state["vector_store"] = create_vector_store(app_state["pinecone_client"], texts)
            app_state["processed_documents"].append(web_url)
            
        return {"sources": app_state["processed_documents"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing URL: {str(e)}")

@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    """Process a chat message and return response"""
    prompt = request.content
    force_web_search = request.force_web_search
    
    # Process and respond to the message
    try:
        # Check for URLs in prompt
        url_detector = test_url_detector(prompt)
        detected_urls = url_detector.urls
        
        # Process any detected URLs
        for url in detected_urls:
            if url not in app_state["processed_documents"]:
                texts = process_web(url)
                if texts and app_state["pinecone_client"]:
                    if app_state["vector_store"]:
                        app_state["vector_store"].add_documents(texts)
                    else:
                        app_state["vector_store"] = create_vector_store(app_state["pinecone_client"], texts)
                    app_state["processed_documents"].append(url)
        
        # Rewrite the query for better retrieval
        query_rewriter = get_query_rewriter_agent()
        rewritten_query = query_rewriter.run(prompt).content
        
        # Choose search strategy
        context = ""
        search_links = []
        source_docs = []
        
        if not force_web_search and app_state["vector_store"]:
            # Try document search first
            has_relevant_docs, docs = check_document_relevance(
                rewritten_query,
                app_state["vector_store"],
                SIMILARITY_THRESHOLD
            )
            
            if docs:
                context = "\n\n".join([d.page_content for d in docs])
                source_docs = docs
        
        # Use Google search if applicable
        if (force_web_search or not context):
            search_results, search_links = google_search(rewritten_query)
            if search_results:
                context = f"Google Search Results:\n{search_results}"
        
        # Generate response using the RAG agent
        rag_agent = get_rag_agent()
        
        if context:
            full_prompt = f"""Context: {context}

Original Question: {prompt}
Rewritten Question: {rewritten_query}

"""
            if search_links:
                full_prompt += f"Source Links:\n" + "\n".join([f"- {link}" for link in search_links]) + "\n\n"
            
            full_prompt += "Please provide a comprehensive answer based on the available information."
        else:
            full_prompt = f"Original Question: {prompt}\nRewritten Question: {rewritten_query}"

        response = rag_agent.run(full_prompt)
        
        # Prepare sources for response
        sources = []
        if source_docs:
            for doc in source_docs:
                source_type = doc.metadata.get("source_type", "unknown")
                source_name = doc.metadata.get("file_name", "unknown")
                sources.append({
                    "type": source_type,
                    "name": source_name,
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
        
        if search_links:
            for link in search_links:
                sources.append({
                    "type": "web",
                    "name": link,
                    "content": ""
                })
        
        return {"content": response.content, "sources": sources}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/sources", response_model=SourceResponse)
async def get_sources():
    """Get all processed document sources"""
    return {"sources": app_state["processed_documents"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
