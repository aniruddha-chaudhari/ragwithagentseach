import streamlit as st
import google.generativeai as genai
from typing import List, Tuple
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# Constants
INDEX_NAME = "gemini-thinking-agent-agno"
EMBEDDING_DIMENSION = 768  # Gemini embedding-004 dimension

class GeminiEmbedder(Embeddings):
    def __init__(self, model_name="models/text-embedding-004", api_key=None):
        # Use provided API key or get from session state
        api_key = api_key or st.session_state.get("google_api_key", "")
        genai.configure(api_key=api_key)
        self.model = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        response = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document"
        )
        return response['embedding']


def init_pinecone(api_key=None):
    """Initialize Pinecone client with configured settings."""
    # Use provided API key or get from session state
    api_key = api_key or st.session_state.get("pinecone_api_key", "")
    if not api_key:
        return None
        
    try:
        pc = Pinecone(api_key=api_key)
        
        # Check if index exists, create if not
        existing_indexes = [index.name for index in pc.list_indexes()]
        
        if INDEX_NAME not in existing_indexes:
            pc.create_index(
                name=INDEX_NAME,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            st.success(f"📚 Created new index: {INDEX_NAME}")
            
        return pc
    except Exception as e:
        st.error(f"🔴 Pinecone connection failed: {str(e)}")
        return None


def create_vector_store(pc_client, texts):
    """Create and initialize vector store with documents."""
    try:
        # Initialize vector store
        index = pc_client.Index(INDEX_NAME)
        
        vector_store = PineconeVectorStore(
            index=index,
            embedding=GeminiEmbedder(),
            text_key="text"
        )
        
        # Add documents
        with st.spinner('📤 Uploading documents to Pinecone...'):
            vector_store.add_documents(texts)
            st.success("✅ Documents stored successfully!")
            return vector_store
            
    except Exception as e:
        st.error(f"🔴 Vector store error: {str(e)}")
        return None


def check_document_relevance(query: str, vector_store, threshold: float = 0.7) -> Tuple[bool, List[Document]]:
    """
    Check if documents in vector store are relevant to the query.
    
    Args:
        query: The search query
        vector_store: The vector store to search in
        threshold: Similarity threshold
        
    Returns:
        tuple[bool, List]: (has_relevant_docs, relevant_docs)
    """
    if not vector_store:
        return False, []
        
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": threshold}
    )
    docs = retriever.invoke(query)
    return bool(docs), docs