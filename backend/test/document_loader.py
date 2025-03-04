import tempfile
from datetime import datetime
from typing import List, Tuple, Optional

import streamlit as st
import bs4
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def process_pdf(file) -> List:
    """Process PDF file and add source metadata."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            loader = PyPDFLoader(tmp_file.name)
            documents = loader.load()
            
            # Add source metadata
            for doc in documents:
                doc.metadata.update({
                    "source_type": "pdf",
                    "file_name": file.name,
                    "timestamp": datetime.now().isoformat()
                })
                
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(documents)
            print(f"Number of PDF chunks: {len(chunks)}")  # Print statement
            return chunks
    except Exception as e:
        st.error(f"📄 PDF processing error: {str(e)}")
        return []


def load_web_document(url: str) -> List:
    """
    Load a document from a specified URL using WebBaseLoader.

    Args:
        url (str): The URL of the webpage to load.

    Returns:
        List: The loaded document(s).
    """
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        print(f"Number of web documents loaded: {len(docs)}")  # Print statement
        return docs
    except Exception as e:
        st.error(f"🌐 Web loading error: {str(e)}")
        return []


def extract_title_and_split_content(docs: List) -> Tuple[Optional[str], List]:
    """
    Extract title and split content into chunks using RecursiveCharacterTextSplitter.

    Args:
        docs (List): The documents loaded from WebBaseLoader.

    Returns:
        Tuple[Optional[str], List]: (title, content_chunks)
    """
    if not docs:
        return None, []
    
    # Get title from the first document's metadata
    title = docs[0].metadata.get('title')
    
    # Add source metadata
    for doc in docs:
        doc.metadata.update({
            "source_type": "url",
            "timestamp": datetime.now().isoformat()
        })
    
    # Apply text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    content_chunks = text_splitter.split_documents(docs)
    print(f"Number of content chunks after splitting: {len(content_chunks)}")  # Print statement
    
    return title, content_chunks


def process_web(url: str) -> List:
    """
    Process web URL by loading the document and splitting content into chunks.

    Args:
        url (str): The URL to process.

    Returns:
        List: The processed document chunks.
    """
    docs = load_web_document(url)
    if not docs:
        return []
    
    title, content_chunks = extract_title_and_split_content(docs)
    print(f"Title of the web document: {title}")  # Print statement
    return content_chunks