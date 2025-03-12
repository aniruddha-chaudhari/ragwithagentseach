# Configure imports first
import os
import json
import uuid
import pickle
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
import google.generativeai as genai
from langchain_pinecone import PineconeVectorStore

# Import embedder components before using them
from embedder import (
    init_pinecone,
    create_vector_store,
    check_document_relevance,
    INDEX_NAME,
    GeminiEmbedder,
)

from utils.formaturl import format_url_display
from search import google_search
from agents.intentdetectorAgent import detect_google_search_intent
from document_loader import prepare_document, process_pdf, process_web, process_image
from agents.writeragents import get_query_rewriter_agent, get_rag_agent, test_url_detector

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Constants
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
SIMILARITY_THRESHOLD = 0.7
SESSIONS_DIR = Path("./saved_sessions")

# Initialize API clients first
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)
pinecone_client = init_pinecone(PINECONE_API_KEY)

# Create sessions directory if it doesn't exist
SESSIONS_DIR.mkdir(exist_ok=True)

# Session storage functions
def save_session(session_id: str, session_data: Dict[str, Any]) -> None:
    """Save session data to file"""
    session_file = SESSIONS_DIR / f"{session_id}.pkl"
    with open(session_file, 'wb') as f:
        pickle.dump(session_data, f)

def load_session(session_id: str) -> Dict[str, Any]:
    """Load session data from file"""
    session_file = SESSIONS_DIR / f"{session_id}.pkl"
    if not session_file.exists():
        return None
    
    with open(session_file, 'rb') as f:
        return pickle.load(f)

def get_available_sessions() -> List[str]:
    """Get list of available saved sessions"""
    if not SESSIONS_DIR.exists():
        return []
    return [f.stem for f in SESSIONS_DIR.glob("*.pkl")]

def format_url_display(url, max_length=50):
    """Format URL for display by shortening if needed."""
    if len(url) > max_length:
        # Keep the domain and truncate the path
        domain = url.split('//')[-1].split('/')[0]
        return f"{domain}/...{url[-20:]}"
    return url

def get_session_vector_store():
    """Get or create a vector store for the current session."""
    session_id = st.session_state.chat_session_id
    
    # If the session already has a vector store, return it
    if session_id in st.session_state.session_vector_stores:
        return st.session_state.session_vector_stores[session_id]
    
    # If we have a global vector store, but not for this session,
    # create one with the appropriate namespace
    if pinecone_client:
        # Initialize empty vector store with namespace
        try:
            index = pinecone_client.Index(INDEX_NAME)
            from embedder import INDEX_NAME, GeminiEmbedder
            vector_store = PineconeVectorStore(
                index=index,
                embedding=GeminiEmbedder(),
                text_key="text",
                namespace=session_id
            )
            st.session_state.session_vector_stores[session_id] = vector_store
            return vector_store
        except Exception as e:
            st.error(f"Error initializing vector store: {e}")
    
    return None

def save_current_session():
    """Save the current session state to a file"""
    session_id = st.session_state.chat_session_id
    session_data = {
        "history": st.session_state.history,
        "processed_documents": st.session_state.processed_documents,
        "info_messages": st.session_state.info_messages,
        "rewritten_query": st.session_state.rewritten_query,
        "search_sources": st.session_state.search_sources,
        "doc_sources": st.session_state.doc_sources,
        "use_web_search": st.session_state.use_web_search,
        "session_id": session_id,
    }
    save_session(session_id, session_data)
    
    # Update available sessions list
    st.session_state.available_sessions = get_available_sessions()
    return session_id

def load_session_data(session_id):
    """Load a session from saved file"""
    session_data = load_session(session_id)
    if session_data:
        st.session_state.chat_session_id = session_data.get("session_id", session_id)
        st.session_state.history = session_data.get("history", [])
        st.session_state.processed_documents = session_data.get("processed_documents", [])
        st.session_state.info_messages = session_data.get("info_messages", [])
        st.session_state.rewritten_query = session_data.get("rewritten_query", {"original": "", "rewritten": ""})
        st.session_state.search_sources = session_data.get("search_sources", [])
        st.session_state.doc_sources = session_data.get("doc_sources", [])
        st.session_state.use_web_search = session_data.get("use_web_search", False)
        
        # Get vector store for this session
        st.session_state.vector_store = get_session_vector_store()
        
        return True
    return False

# Streamlit App Initialization
st.title("Agentic Chatbot")

# Session State Initialization
if 'google_api_key' not in st.session_state:
    st.session_state.google_api_key = GOOGLE_API_KEY
if 'pinecone_api_key' not in st.session_state:
    st.session_state.pinecone_api_key = PINECONE_API_KEY
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'use_web_search' not in st.session_state:
    st.session_state.use_web_search = False
if 'force_web_search' not in st.session_state:
    st.session_state.force_web_search = False
if 'similarity_threshold' not in st.session_state:
    st.session_state.similarity_threshold = SIMILARITY_THRESHOLD
# New session state variables to preserve messages
if 'info_messages' not in st.session_state:
    st.session_state.info_messages = []
if 'rewritten_query' not in st.session_state:
    st.session_state.rewritten_query = {"original": "", "rewritten": ""}
if 'search_sources' not in st.session_state:
    st.session_state.search_sources = []
if 'doc_sources' not in st.session_state:
    st.session_state.doc_sources = []
# Chat session namespace management
if 'chat_session_id' not in st.session_state:
    st.session_state.chat_session_id = f"session_{uuid.uuid4().hex[:8]}"
if 'session_vector_stores' not in st.session_state:
    st.session_state.session_vector_stores = {}
if 'available_sessions' not in st.session_state:
    st.session_state.available_sessions = get_available_sessions()


# Sidebar Configuration
st.sidebar.header("⚙️ Configuration")

# Session Management
with st.sidebar.expander("💬 Session Management"):
    st.write(f"Current Session ID: {st.session_state.chat_session_id}")
    
    # Save current session button
    if st.button("💾 Save Current Session"):
        saved_id = save_current_session()
        st.success(f"Session saved as: {saved_id}")
        st.rerun()
    
    # Available sessions dropdown
    available_sessions = st.session_state.available_sessions
    if available_sessions:
        selected_session = st.selectbox(
            "Load Previous Session", 
            options=available_sessions,
            format_func=lambda x: f"Session {x}"
        )
        
        if st.button("📂 Load Selected Session"):
            if load_session_data(selected_session):
                st.success(f"Loaded session: {selected_session}")
                st.rerun()
            else:
                st.error(f"Failed to load session: {selected_session}")
    
    # Option to create a new session
    if st.button("🆕 New Session"):
        # Save current session before creating a new one
        save_current_session()
        
        # Generate a new session ID
        new_session_id = f"session_{uuid.uuid4().hex[:8]}"
        st.session_state.chat_session_id = new_session_id
        st.session_state.history = []
        st.session_state.info_messages = []
        st.session_state.rewritten_query = {"original": "", "rewritten": ""}
        st.session_state.search_sources = []
        st.session_state.doc_sources = []
        st.session_state.vector_store = None
        st.session_state.processed_documents = []
        st.success(f"Created new session: {new_session_id}")
        st.rerun()

# Clear Chat Button
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.history = []
    st.session_state.info_messages = []
    st.session_state.rewritten_query = {"original": "", "rewritten": ""}
    st.session_state.search_sources = []
    st.session_state.doc_sources = []
    st.rerun()

# Web Search Configuration
st.sidebar.header("🌐 Web Search Configuration")
st.session_state.use_web_search = st.sidebar.checkbox("Enable Google Search", value=st.session_state.use_web_search)

# Set up API keys
os.environ["GOOGLE_API_KEY"] = st.session_state.google_api_key
genai.configure(api_key=st.session_state.google_api_key)
pinecone_client = init_pinecone(st.session_state.pinecone_api_key)

# Display chat history (moved to top of app flow)
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Display source information right after chat history
# Show document sources if available
if st.session_state.doc_sources:
    with st.expander("🔍 See document sources"):
        for i, doc in enumerate(st.session_state.doc_sources, 1):
            source_type = doc["source_type"]
            if source_type == "image":
                source_icon = "🖼️"
            elif source_type == "document":
                source_icon = "📄"
            else:
                source_icon = "🌐"
            st.write(f"{source_icon} Source {i} from {doc['source_name']}:")
            st.write(doc["content"])

# Show search links if available
if st.session_state.search_sources:
    with st.expander("🔗 Web Search Sources"):
        for i, link in enumerate(st.session_state.search_sources, 1):
            display_link = format_url_display(link)
            st.write(f"{i}. [{display_link}]({link})")

# Display persistent info messages
for message in st.session_state.info_messages:
    st.info(message)

# Display rewritten query if available
if st.session_state.rewritten_query["original"]:
    with st.expander("🔄 See rewritten query"):
        st.write(f"Original: {st.session_state.rewritten_query['original']}")
        st.write(f"Rewritten: {st.session_state.rewritten_query['rewritten']}")

# Main Application Flow
# File/URL Upload Section
st.sidebar.header("📁 Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload Document", type=["pdf", "png", "jpg", "jpeg", "gif", "webp"])
web_url = st.sidebar.text_input("Or enter URL")

# Process documents using unified approach
if uploaded_file:
    file_name = uploaded_file.name
    if file_name not in st.session_state.processed_documents:
        with st.spinner('Processing document...'):
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Process based on file type
            if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                texts = process_image(uploaded_file)
                doc_type = "Image"
            else:  # PDF or other document types
                texts = process_pdf(uploaded_file)
                doc_type = "Document"
                
            if texts and pinecone_client:
                # Create or get vector store with session namespace
                session_id = st.session_state.chat_session_id
                if st.session_state.vector_store:
                    # Update existing vector store with session namespace
                    vector_store = create_vector_store(pinecone_client, texts, namespace=session_id)
                else:
                    vector_store = create_vector_store(pinecone_client, texts, namespace=session_id)
                    
                st.session_state.vector_store = vector_store
                st.session_state.session_vector_stores[session_id] = vector_store
                st.session_state.processed_documents.append(file_name)
                st.success(f"✅ Added {doc_type}: {file_name} to session {session_id}")

if web_url:
    if web_url not in st.session_state.processed_documents:
        with st.spinner('Processing URL...'):
            texts = process_web(web_url)
            if texts and pinecone_client:
                # Create or get vector store with session namespace
                session_id = st.session_state.chat_session_id
                if st.session_state.vector_store:
                    # Update existing vector store with session namespace
                    vector_store = create_vector_store(pinecone_client, texts, namespace=session_id)
                else:
                    vector_store = create_vector_store(pinecone_client, texts, namespace=session_id)
                    
                st.session_state.vector_store = vector_store
                st.session_state.session_vector_stores[session_id] = vector_store
                st.session_state.processed_documents.append(web_url)
                st.success(f"✅ Added URL: {web_url} to session {session_id}")

# Display sources in sidebar with appropriate icons
if st.session_state.processed_documents:
    st.sidebar.header("📚 Processed Sources")
    for source in st.session_state.processed_documents:
        if source.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            st.sidebar.text(f"🖼️ {source}")
        elif source.endswith('.pdf'):
            st.sidebar.text(f"📄 {source}")
        else:
            st.sidebar.text(f"🌐 {source}")

# Chat Interface - Replace with form-based approach
# Create two columns for chat input and search toggle
with st.form(key="chat_form", clear_on_submit=True):
    chat_col, toggle_col = st.columns([0.9, 0.1])
    
    with chat_col:
        prompt = st.text_input("Ask about your documents...", key="chat_input")
    
    with toggle_col:
        force_web_search = st.checkbox('🌐', value=st.session_state.force_web_search, 
                                      help="Force Google search")
    
    submit_button = st.form_submit_button("Send")
    
    if submit_button and prompt:
        # Clear previous messages
        st.session_state.info_messages = []
        st.session_state.rewritten_query = {"original": "", "rewritten": ""}
        st.session_state.search_sources = []
        st.session_state.doc_sources = []
        
        # Update the force search toggle state
        st.session_state.force_web_search = force_web_search
        
        # Make sure we have the session's vector store
        session_vector_store = get_session_vector_store()
        if session_vector_store:
            st.session_state.vector_store = session_vector_store
        
        # Add user message to history
        st.session_state.history.append({"role": "user", "content": prompt})
        
        # Process query (the existing logic)
        with st.spinner("🔍 Checking for URLs..."):
            try:
                url_detector = test_url_detector(prompt)
                detected_urls = url_detector.urls
                
                # Process any detected URLs
                if detected_urls:
                    st.toast(f"📎 Found {len(detected_urls)} URLs in your query. Processing them...")
                    
                    for url in detected_urls:
                        if url not in st.session_state.processed_documents:
                            with st.spinner(f'Processing URL: {url}...'):
                                texts = process_web(url)
                                if texts and pinecone_client:
                                    # Use session namespace
                                    session_id = st.session_state.chat_session_id
                                    if st.session_state.vector_store:
                                        vector_store = create_vector_store(pinecone_client, texts, namespace=session_id)
                                    else:
                                        vector_store = create_vector_store(pinecone_client, texts, namespace=session_id)
                                    
                                    st.session_state.vector_store = vector_store
                                    st.session_state.session_vector_stores[session_id] = vector_store
                                    st.session_state.processed_documents.append(url)
                                    st.toast(f"✅ Added URL from query: {url}")
            
            except Exception as e:
                st.error(f"❌ Error processing URLs: {str(e)}")
                # Continue with original prompt if URL detection fails
                

        # Step 1: Rewrite the query for better retrieval (continue with existing code)
        with st.spinner("🤔 Reformulating query..."):
            try:
                query_rewriter = get_query_rewriter_agent()
                rewritten_query = query_rewriter.run(prompt).content
                
                # Save for display after rerun
                st.session_state.rewritten_query = {
                    "original": prompt,
                    "rewritten": rewritten_query
                }
            except Exception as e:
                st.error(f"❌ Error rewriting query: {str(e)}")
                rewritten_query = prompt

        # Step 2: Choose search strategy based on force_web_search toggle
        context = ""
        search_links = []
        docs = []
        search_intent_detected = False

        # Check if query needs web search based on intent detection
        with st.spinner("🧠 Analyzing query intent..."):
            try:
                search_intent_detected = detect_google_search_intent(rewritten_query)
                if search_intent_detected and not st.session_state.use_web_search:
                    # Only toggle and notify if web search wasn't already enabled
                    st.session_state.use_web_search = True
                    st.toast("🔄 Automatically enabling web search based on query needs", icon="ℹ️")
            except Exception as e:
                st.error(f"❌ Error detecting search intent: {str(e)}")
                # Fall back to regular behavior if intent detection fails

        # First, try document search if not forcing web search
        if not st.session_state.force_web_search and st.session_state.vector_store:
            # Try document search with session namespace
            session_id = st.session_state.chat_session_id
            has_relevant_docs, docs = check_document_relevance(
                rewritten_query, 
                st.session_state.vector_store, 
                st.session_state.similarity_threshold,
                namespace=session_id
            )
            if docs:
                context = "\n\n".join([d.page_content for d in docs])
                st.toast(f"📊 Found {len(docs)} relevant documents")
                # Save doc sources for display
                st.session_state.doc_sources = [
                    {
                        "source_type": doc.metadata.get("source_type", "unknown"),
                        "source_name": doc.metadata.get("file_name", "unknown"),
                        "content": doc.page_content[:200] + "..."
                    }
                    for doc in docs
                ]
            elif st.session_state.use_web_search and search_intent_detected:
                st.toast("🔄 No relevant documents found, using web search...")

        # Step 3: Use Google search if:
        # 1. Web search is forced ON via toggle, or
        # 2. No relevant documents found AND web search is enabled AND intent detection suggests it, or
        # 3. Web search is enabled AND search intent is detected (regardless of documents)
        should_use_web_search = (
            st.session_state.force_web_search or 
            (not docs and st.session_state.use_web_search and search_intent_detected) or
            (st.session_state.use_web_search and search_intent_detected)
        )
        
        # Remove redundant debug information
        # st.session_state.info_messages.append(f"🔄 Web search enabled: {st.session_state.use_web_search}")
        # st.session_state.info_messages.append(f"🔄 Intent detection result: {search_intent_detected}")
        # st.session_state.info_messages.append(f"🔄 Using web search: {should_use_web_search}")
        
        if should_use_web_search:
            with st.spinner("🔍 Searching with Google..."):
                try:
                    search_results, search_links = google_search(rewritten_query)
                    if search_results:
                        # If we have both doc results and search results, combine them
                        if context:
                            context = f"{context}\n\n--- Additional Information from Google Search ---\n\n{search_results}"
                        else:
                            context = f"Google Search Results:\n{search_results}"
                            
                        if st.session_state.force_web_search:
                            st.toast("ℹ️ Using Google search as requested", icon="🌐")
                        
                        # Save search links for display after rerun
                        st.session_state.search_sources = search_links
                except Exception as e:
                    st.error(f"❌ Google search error: {str(e)}")

        # Step 4: Generate response using the RAG agent
        with st.spinner("🤖 Thinking..."):
            try:
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
                    st.session_state.info_messages.append("ℹ️ No relevant information found in documents or Google search.")

                response = rag_agent.run(full_prompt)
                
                # Add assistant response to history
                st.session_state.history.append({
                    "role": "assistant",
                    "content": response.content
                })
            except Exception as e:
                st.error(f"❌ Error generating response: {str(e)}")
                
        # Rerun after processing to show updated chat
        st.rerun()