# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys with fallbacks (these are used if not overridden by environment variables)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Chatbot configuration
SIMILARITY_THRESHOLD = 0.7
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
USE_WEB_SEARCH_DEFAULT = True
VECTOR_INDEX_NAME = "gemini-thinking-agent-agno"

# Web scraping configuration
BASE_URL = "https://www.theknot.com/marketplace/wedding-reception-venues-atlanta-ga"
CSS_SELECTOR = "[class^='info-container']"
REQUIRED_KEYS = [
    "name",
    "price",
    "location",
    "capacity",
    "rating",
    "reviews",
    "description",
]

# Document processing configuration
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
DEFAULT_CRAWLER_SESSION_ID = "default_web_crawler_session"
DEFAULT_BROWSER_TYPE = "chromium"
BROWSER_HEADLESS_MODE = True
BROWSER_VERBOSE_MODE = False

# LLM models
GEMINI_EMBEDDING_MODEL = "models/embedding-001"
GEMINI_CHAT_MODEL = "gemini-2.0-flash"
GEMINI_PRO_MODEL = "gemini-2.0-pro"
DEEPSEEK_MODEL = "groq/deepseek-r1-distill-llama-70b"

# Document analysis prompts
IMAGE_ANALYSIS_PROMPT = """
Please analyze and describe this image in detail. Include:
1. Type of content and main subject
2. Key information or features
3. Visual elements and their significance
4. Any text present in the image
5. Overall meaning and context
"""

DOCUMENT_ANALYSIS_PROMPT = """
Please analyze and summarize this document in detail. Include:
1. Type of content and main subject
2. Key information or facts
3. Structure and organization
4. Main arguments or points
5. Overall context and significance
"""
