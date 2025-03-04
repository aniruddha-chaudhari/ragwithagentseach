from typing import List, Dict, Any

def add_to_history(history: List[Dict[str, Any]], role: str, content: str) -> List[Dict[str, Any]]:
    """Add a message to chat history in the format Gemini expects"""
    history.append({
        "role": role,
        "parts": [content]
    })
    return history

def format_document_context(history: List[Dict[str, Any]], filename: str, content: str) -> List[Dict[str, Any]]:
    """Format document content in chat history"""
    history = add_to_history(history, "user", f"Document uploaded: {filename}")
    history = add_to_history(history, "assistant", content)
    return history