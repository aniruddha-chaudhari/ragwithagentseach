import os
import json
from typing import List
from dotenv import load_dotenv

import streamlit as st
import google.generativeai as genai

# Import shared functionality from embedder.py
from embedder import (
    init_pinecone,
    create_vector_store,
    check_document_relevance,
)

from search import google_search

# Import document processing functions - now with unified approach
from document_loader import prepare_document, process_pdf, process_web, process_image

# Import agents
from agents.writeragents import get_query_rewriter_agent, get_rag_agent, test_url_detector

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

# Display chat history (moved to top of app flow)
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Helper functions
def format_url_display(url, max_length=50):
    """Format URL for display by shortening if needed."""
    if len(url) > max_length:
        # Keep the domain and truncate the path
        domain = url.split('//')[-1].split('/')[0]
        return f"{domain}/...{url[-20:]}"
    return url

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
                if st.session_state.vector_store:
                    st.session_state.vector_store.add_documents(texts)
                else:
                    st.session_state.vector_store = create_vector_store(pinecone_client, texts)
                st.session_state.processed_documents.append(file_name)
                st.success(f"✅ Added {doc_type}: {file_name}")

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
        # Update the force search toggle state
        st.session_state.force_web_search = force_web_search
        
        # Add user message to history
        st.session_state.history.append({"role": "user", "content": prompt})
        
        # Process query (the existing logic)
        with st.spinner("🔍 Checking for URLs..."):
            try:
                url_detector = test_url_detector(prompt)
                detected_urls = url_detector.urls
                
                # Process any detected URLs
                if detected_urls:
                    st.info(f"📎 Found {len(detected_urls)} URLs in your query. Processing them...")
                    
                    for url in detected_urls:
                        if url not in st.session_state.processed_documents:
                            with st.spinner(f'Processing URL: {url}...'):
                                texts = process_web(url)
                                if texts and pinecone_client:
                                    if st.session_state.vector_store:
                                        st.session_state.vector_store.add_documents(texts)
                                    else:
                                        st.session_state.vector_store = create_vector_store(pinecone_client, texts)
                                    st.session_state.processed_documents.append(url)
                                    st.success(f"✅ Added URL from query: {url}")
            
            except Exception as e:
                st.error(f"❌ Error processing URLs: {str(e)}")
                # Continue with original prompt if URL detection fails
                

        # Step 1: Rewrite the query for better retrieval (continue with existing code)
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
                                    display_link = format_url_display(link)
                                    st.write(f"{i}. [{display_link}]({link})")
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
                                if source_type == "image":
                                    source_icon = "🖼️"
                                elif source_type == "document":
                                    source_icon = "📄"
                                else:
                                    source_icon = "🌐"
                                source_name = doc.metadata.get("file_name", "unknown")
                                st.write(f"{source_icon} Source {i} from {source_name}:")
                                st.write(f"{doc.page_content[:200]}...")
                    
                    # Show search links if it came from web search
                    elif search_links:
                        with st.expander("🔗 Web Search Sources"):
                            for i, link in enumerate(search_links, 1):
                                display_link = format_url_display(link)
                                st.write(f"{i}. [{display_link}]({link})")

            except Exception as e:
                st.error(f"❌ Error generating response: {str(e)}")
                
        # Rerun after processing to show updated chat
        st.rerun()
