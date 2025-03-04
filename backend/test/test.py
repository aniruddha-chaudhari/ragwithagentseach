import os
from typing import List
from dotenv import load_dotenv

import streamlit as st
import google.generativeai as genai
from agno.agent import Agent
from agno.models.google import Gemini

# Import shared functionality from embedder.py
from embedder import (
    init_pinecone,
    create_vector_store,
    check_document_relevance,
)

from search import google_search

# Import document processing functions
from document_loader import process_pdf, process_web

# Load environment variables
load_dotenv()

# Get API keys from environment variables with fallbacks
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")

# Check if API keys are available
if not GOOGLE_API_KEY:
    st.error("Missing GEMINI_API_KEY in environment variables")
if not PINECONE_API_KEY:
    st.error("Missing PINECONE_API_KEY in environment variables")

# Hardcoded similarity threshold - 0.7 is a good balance between precision and recall
SIMILARITY_THRESHOLD = 0.7


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


# Sidebar Configuration
st.sidebar.header("⚙️ Configuration")

# Clear Chat Button
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.history = []
    st.rerun()

# Web Search Configuration
st.sidebar.header("🌐 Web Search Configuration")
st.session_state.use_web_search = st.sidebar.checkbox("Enable Google Search", value=st.session_state.use_web_search)

# Set up API keys
os.environ["GOOGLE_API_KEY"] = st.session_state.google_api_key
genai.configure(api_key=st.session_state.google_api_key)
pinecone_client = init_pinecone(st.session_state.pinecone_api_key)

# Rest of your functions remain unchanged
def get_query_rewriter_agent() -> Agent:
    """Initialize a query rewriting agent."""
    return Agent(
        name="Query Rewriter",
        model=Gemini(id="gemini-2.0-flash"),
        instructions="""You are an expert at reformulating questions to be more precise and detailed. 
        Your task is to:
        1. Analyze the user's question
        2. Rewrite it to be more specific and search-friendly
        3. Expand any acronyms or technical terms
        4. Return ONLY the rewritten query without any additional text or explanations
        
        """,
        show_tool_calls=False,
        markdown=True,
    )


def get_rag_agent() -> Agent:
    """Initialize the main RAG agent."""
    return Agent(
        name="Gemini RAG Agent",
        model=Gemini(id="gemini-2.0-flash"),
        instructions="""You are an Intelligent Agent specializing in providing accurate answers.
        
        When given context from documents:
        - Focus on information from the provided documents
        - Be precise and cite specific details
        
        When given web search results:
        - Clearly indicate that the information comes from Google Search
        - Synthesize the information clearly
        - Reference the provided source links when possible
        
        Always maintain high accuracy and clarity in your responses.
        """,
        show_tool_calls=True,
        markdown=True,
    )


# Main Application Flow
# File/URL Upload Section
st.sidebar.header("📁 Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
web_url = st.sidebar.text_input("Or enter URL")

# Process documents
if uploaded_file:
    file_name = uploaded_file.name
    if file_name not in st.session_state.processed_documents:
        with st.spinner('Processing PDF...'):
            texts = process_pdf(uploaded_file)
            if texts and pinecone_client:
                if st.session_state.vector_store:
                    st.session_state.vector_store.add_documents(texts)
                else:
                    st.session_state.vector_store = create_vector_store(pinecone_client, texts)
                st.session_state.processed_documents.append(file_name)
                st.success(f"✅ Added PDF: {file_name}")

if web_url:
    if web_url not in st.session_state.processed_documents:
        with st.spinner('Processing URL...'):
            texts = process_web(web_url)
            if texts and pinecone_client:
                if st.session_state.vector_store:
                    st.session_state.vector_store.add_documents(texts)
                else:
                    st.session_state.vector_store = create_vector_store(pinecone_client, texts)
                st.session_state.processed_documents.append(web_url)
                st.success(f"✅ Added URL: {web_url}")

# Display sources in sidebar
if st.session_state.processed_documents:
    st.sidebar.header("📚 Processed Sources")
    for source in st.session_state.processed_documents:
        if source.endswith('.pdf'):
            st.sidebar.text(f"📄 {source}")
        else:
            st.sidebar.text(f"🌐 {source}")

# Chat Interface
# Create two columns for chat input and search toggle
chat_col, toggle_col = st.columns([0.9, 0.1])

with chat_col:
    prompt = st.chat_input("Ask about your documents...")

with toggle_col:
    st.session_state.force_web_search = st.toggle('🌐', help="Force Google search")

if prompt:
    # Add user message to history
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Step 1: Rewrite the query for better retrieval
    with st.spinner("🤔 Reformulating query..."):
        try:
            query_rewriter = get_query_rewriter_agent()
            rewritten_query = query_rewriter.run(prompt).content
            
            with st.expander("🔄 See rewritten query"):
                st.write(f"Original: {prompt}")
                st.write(f"Rewritten: {rewritten_query}")
        except Exception as e:
            st.error(f"❌ Error rewriting query: {str(e)}")
            rewritten_query = prompt

    # Step 2: Choose search strategy based on force_web_search toggle
    context = ""
    search_links = []
    docs = []
    if not st.session_state.force_web_search and st.session_state.vector_store:
        # Try document search first
        has_relevant_docs, docs = check_document_relevance(
            rewritten_query, 
            st.session_state.vector_store, 
            st.session_state.similarity_threshold
        )
        if docs:
            context = "\n\n".join([d.page_content for d in docs])
            st.info(f"📊 Found {len(docs)} relevant documents (similarity > {st.session_state.similarity_threshold})")
        elif st.session_state.use_web_search:
            st.info("🔄 No relevant documents found in database, falling back to Google search...")

    # Step 3: Use Google search if:
    # 1. Web search is forced ON via toggle, or
    # 2. No relevant documents found AND web search is enabled in settings
    if (st.session_state.force_web_search or not context) and st.session_state.use_web_search:
        with st.spinner("🔍 Searching with Google..."):
            try:
                search_results, search_links = google_search(rewritten_query)
                if search_results:
                    context = f"Google Search Results:\n{search_results}"
                    if st.session_state.force_web_search:
                        st.info("ℹ️ Using Google search as requested via toggle.")
                    else:
                        st.info("ℹ️ Using Google search as fallback since no relevant documents were found.")
                    
                    # Display source links if available
                    if search_links:
                        with st.expander("🔗 Search Source Links"):
                            for i, link in enumerate(search_links, 1):
                                st.write(f"{i}. [{link}]({link})")
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
                st.info("ℹ️ No relevant information found in documents or Google search.")

            response = rag_agent.run(full_prompt)
            
            # Add assistant response to history
            st.session_state.history.append({
                "role": "assistant",
                "content": response.content
            })
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(response.content)
                
                # Show document sources if available
                if not st.session_state.force_web_search and 'docs' in locals() and docs:
                    with st.expander("🔍 See document sources"):
                        for i, doc in enumerate(docs, 1):
                            source_type = doc.metadata.get("source_type", "unknown")
                            source_icon = "📄" if source_type == "pdf" else "🌐"
                            source_name = doc.metadata.get("file_name" if source_type == "pdf" else "url", "unknown")
                            st.write(f"{source_icon} Source {i} from {source_name}:")
                            st.write(f"{doc.page_content[:200]}...")
                
                # Show search links if it came from web search
                elif search_links:
                    with st.expander("🔗 Web Search Sources"):
                        for i, link in enumerate(search_links, 1):
                            st.write(f"{i}. [{link}]({link})")

        except Exception as e:
            st.error(f"❌ Error generating response: {str(e)}")