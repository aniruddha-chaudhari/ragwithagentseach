import tempfile
from datetime import datetime
import asyncio
from typing import List, Tuple, Optional
import os

import streamlit as st
import bs4
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from google import genai

# Import crawler components
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from utils.scraper_utils import get_browser_config, get_llm_strategy, fetch_and_process_page

# Import centralized configuration
from config import (
    GEMINI_API_KEY,
    GEMINI_CHAT_MODEL,
    SUPPORTED_IMAGE_FORMATS,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    IMAGE_ANALYSIS_PROMPT,
    DOCUMENT_ANALYSIS_PROMPT,
    DEFAULT_CRAWLER_SESSION_ID,
    DEEPSEEK_MODEL,
)

# Import the search function
from search import google_search


def prepare_document(file_path: str) -> List[Document]:
    """
    Processes any document type using Gemini API and returns it in a format
    compatible with the vector storage system.
    
    Args:
        file_path (str): Path to the document file
        
    Returns:
        List[Document]: List containing the processed document
    """
    try:
        # Use API key from session state or environment
        api_key = st.session_state.get("google_api_key", GEMINI_API_KEY)
        client = genai.Client(api_key=api_key)
        
        # Upload the file
        uploaded_file = client.files.upload(file=file_path)
        
        # Determine appropriate prompt based on file type
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in SUPPORTED_IMAGE_FORMATS:
            prompt = IMAGE_ANALYSIS_PROMPT
            source_type = "image"
        else:
            prompt = DOCUMENT_ANALYSIS_PROMPT
            source_type = "document"
        
        # Generate content
        response = client.models.generate_content(
            model=GEMINI_CHAT_MODEL,
            contents=[uploaded_file, prompt],
        )
        
        content = response.text
        print(f"Generated content length: {len(content)}")
        
        # Create a Document object
        doc = Document(
            page_content=content,
            metadata={
                "source_type": source_type,
                "file_name": os.path.basename(file_path),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Apply text splitting
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP
        )
        chunks = text_splitter.split_documents([doc])
        print(f"Number of document chunks: {len(chunks)}")
        
        return chunks
        
    except Exception as e:
        st.error(f"📄 Document processing error: {str(e)}")
        return []

# Keep existing functions for backward compatibility
def process_pdf(file) -> List:
    """Process PDF file and add source metadata."""
    try:
        file_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            file_path = tmp_file.name
            
        # Use the new document processor instead
        return prepare_document(file_path)
    except Exception as e:
        st.error(f"📄 PDF processing error: {str(e)}")
        return []


async def load_web_document_async(url: str, session_id: str = None, use_llm: bool = True, 
                                 css_selector: str = None, extract_images: bool = True) -> List[Document]:
    """
    Load a document from a specified URL using crawl4ai AsyncWebCrawler.
    Enhanced version that can optionally use LLM for content extraction and processing.

    Args:
        url (str): The URL of the webpage to load.
        session_id (str): Session identifier for the crawler.
        use_llm (bool): Whether to use LLM for processing content.
        css_selector (str): Optional CSS selector to extract specific content.
        extract_images (bool): Whether to extract images from the webpage.

    Returns:
        List[Document]: The loaded documents.
    """
    try:
        # Use default session ID if none provided
        if session_id is None:
            session_id = DEFAULT_CRAWLER_SESSION_ID
            
        # Get browser configuration
        browser_config = get_browser_config()
        
        # Get LLM strategy if needed
        llm_strategy = get_llm_strategy() if use_llm else None
        
        # Crawl the webpage
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # First, get the general content without LLM processing
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,  # Don't use cached content
                    session_id=session_id,
                    css_selector=css_selector,  # Apply this CSS selector if provided
                ),
            )
            
            if not result.success:
                print(f"Failed to crawl {url}: {result.error_message}")
                return []
            
            content = result.cleaned_html
            title = extract_title_from_html(content)
            
            # Extract images via the crawler capabilities
            image_urls = []
            image_metadata = []
            
            if extract_images:
                soup = bs4.BeautifulSoup(content, "html.parser")
                
                # Find img tags
                img_tags = soup.find_all('img')
                # Also find picture elements and background images
                picture_tags = soup.find_all('picture')
                elements_with_bg = soup.select('[style*="background-image"]')
                
                # Process standard img tags
                for img in img_tags:
                    src = img.get('src', '')
                    # Skip empty sources, data URIs, or very small images
                    if not src or src.startswith('data:'):
                        continue
                        
                    # Convert relative URLs to absolute URLs if needed
                    if src.startswith('/') or not (src.startswith('http://') or src.startswith('https://')):
                        from urllib.parse import urljoin
                        src = urljoin(url, src)
                        
                    # Get image dimensions if available
                    width = img.get('width', '')
                    height = img.get('height', '')
                    alt = img.get('alt', '')
                    
                    # Skip very small images (likely icons)
                    if (width and int(width) < 100) or (height and int(height) < 100):
                        continue
                        
                    image_urls.append(src)
                    
                    # Collect more detailed metadata about each image
                    image_metadata.append({
                        "url": src,
                        "alt_text": alt,
                        "width": width,
                        "height": height,
                        "type": "img_tag"
                    })
                
                # Process picture elements
                for picture in picture_tags:
                    img = picture.find('img')  # Fallback image
                    sources = picture.find_all('source')
                    
                    # Add fallback image
                    if img.get('src') is not None:
                        src = img.get('src')
                        if src.startswith('/') or not (src.startswith('http://') or src.startswith('https://')):
                            from urllib.parse import urljoin
                            src = urljoin(url, src) 
                        
                        alt = img.get('alt', '')
                        
                        image_urls.append(src)
                        image_metadata.append({
                            "url": src,
                            "alt_text": alt,
                            "type": "picture_element"
                        })
                    
                    # Add sources
                    for source in sources:
                        srcset = source.get('srcset', '')
                        if srcset:
                            # Parse srcset for first available source
                            src_url = srcset.split()[0]
                            # Make absolute if relative
                            if src_url.startswith('/') or not (src_url.startswith('http://') or src_url.startswith('https://')):
                                from urllib.parse import urljoin
                                src_url = urljoin(url, src_url)

                            image_urls.append(src_url)
                            image_metadata.append({
                                "url": src_url,
                                "media": source.get('media', ''),
                                "type": "picture_source"
                            })
                
                # Extract background images from style attributes
                import re
                for element in elements_with_bg:
                    style = element.get('style', '')
                    # Use regex to find URLs in background-image styles
                    bg_urls = re.findall(r'background-image:.*?url\(["\']?([^"\']*)["\']?\)', style)
                    for bg_url in bg_urls:
                        if bg_url.startswith('/') or not (bg_url.startswith('http://') or bg_url.startswith('https://')):
                            from urllib.parse import urljoin
                            bg_url = urljoin(url, bg_url)

                        image_urls.append(bg_url)
                        image_metadata.append({
                            "url": bg_url,
                            "type": "background_image"
                        })

                # Remove duplicates
                unique_urls = []
                unique_metadata = []
                seen_urls = set()
                for i, img_url in enumerate(image_urls):
                    if img_url not in seen_urls:
                        seen_urls.add(img_url)
                        unique_urls.append(img_url)
                        unique_metadata.append(image_metadata[i])
                
                image_urls = unique_urls
                image_metadata = unique_metadata
                
                print(f"Found {len(image_urls)} images on the webpage")
            
            # Use LLM to summarize or process the content if requested
            if use_llm and llm_strategy:
                try:
                    # Include information about images in the prompt
                    image_info = ""
                    if image_urls:
                        image_info = f"\n\nThe page contains {len(image_urls)} images."
                    
                    processed_content = await llm_strategy.process_text(
                        f"Summarize and extract key information from this webpage content: {content[:10000]}...{image_info}",
                        model=DEEPSEEK_MODEL
                    )
                    
                    # Add the LLM-processed content
                    doc_llm = Document(
                        page_content=processed_content,
                        metadata={
                            "source_type": "web_page_llm",
                            "url": url,
                            "title": title,
                            "timestamp": datetime.now().isoformat(),
                            "processing": "llm_summary",
                            "images": image_urls,
                            "image_details": image_metadata if image_metadata else None
                        }
                    )
                    
                    return [doc_llm]
                    
                except Exception as e:
                    print(f"LLM processing error: {e}")
                    # Fall back to regular content if LLM fails
            
            # Create document with the page content
            doc = Document(
                page_content=content,
                metadata={
                    "source_type": "web_page",
                    "url": url,
                    "title": title,
                    "timestamp": datetime.now().isoformat(),
                    "images": image_urls,
                    "image_details": image_metadata if image_metadata else None
                }
            )
            
            print(f"Crawled web page: {url}")
            return [doc]
        
    except Exception as e:
        print(f"🌐 Web loading error: {str(e)}")
        return []

def load_web_document(url: str, use_llm: bool = False, css_selector: str = None) -> List:
    """
    Synchronous wrapper for async web document loader.

    Args:
        url (str): The URL of the webpage to load.
        use_llm (bool): Whether to use LLM for processing content.
        css_selector (str): Optional CSS selector to extract specific content.

    Returns:
        List: The loaded document(s).
    """
    try:
        # Use session ID based on the URL to make it unique but consistent
        session_id = f"session_{hash(url) % 10000}"
        return asyncio.run(load_web_document_async(url, session_id, use_llm, css_selector))
    except Exception as e:
        st.error(f"🌐 Web loading error: {str(e)}")
        return []

def extract_title_from_html(html_content: str) -> str:
    """Extract title from HTML content."""
    try:
        soup = bs4.BeautifulSoup(html_content, "html.parser")
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.text.strip()
        # Fallback to first h1 if no title tag
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.text.strip()
        return "Untitled Document"
    except Exception as e:
        print(f"Error extracting title: {e}")
        return "Untitled Document"

async def scrape_images_from_urls(urls: List[str], limit_per_url: int = 5, max_urls: int = 3) -> List[dict]:
    """
    Scrape images from a list of URLs using the same logic as load_web_document_async.
    
    Args:
        urls (List[str]): List of URLs to scrape images from
        limit_per_url (int): Maximum number of images to extract per URL
        max_urls (int): Maximum number of URLs to process
        
    Returns:
        List[Dict]: List of image metadata dictionaries
    """
    all_images = []
    browser_config = get_browser_config()
    
    # Limit the number of URLs to process for performance
    urls_to_process = urls[:max_urls] if max_urls else urls
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls_to_process:
            try:
                # Use a unique session ID for each URL
                session_id = f"img_session_{hash(url) % 10000}"
                
                # Crawl the webpage
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        session_id=session_id,
                    ),
                )
                
                if not result.success:
                    print(f"Failed to crawl {url} for images: {result.error_message}")
                    continue
                
                content = result.cleaned_html
                
                # Extract images
                image_metadata = []
                
                soup = bs4.BeautifulSoup(content, "html.parser")
                
                # Find img tags
                img_tags = soup.find_all('img')
                # Also find picture elements and background images
                picture_tags = soup.find_all('picture')
                elements_with_bg = soup.select('[style*="background-image"]')
                
                # Process standard img tags
                for img in img_tags:
                    src = img.get('src', '')
                    # Skip empty sources, data URIs, or very small images
                    if not src or src.startswith('data:'):
                        continue
                        
                    # Convert relative URLs to absolute URLs if needed
                    if src.startswith('/') or not (src.startswith('http://') or src.startswith('https://')):
                        from urllib.parse import urljoin
                        src = urljoin(url, src)
                        
                    # Get image dimensions if available
                    width = img.get('width', '')
                    height = img.get('height', '')
                    alt = img.get('alt', '')
                    
                    # Skip very small images (likely icons)
                    if (width and int(width) < 100) or (height and int(height) < 100):
                        continue
                    
                    image_metadata.append({
                        "url": src,
                        "alt_text": alt,
                        "width": width,
                        "height": height,
                        "type": "img_tag",
                        "source_page": url
                    })
                
                # Process picture elements
                for picture in picture_tags:
                    img = picture.find('img')  # Fallback image
                    if img and img.get('src') is not None:
                        src = img.get('src')
                        if src.startswith('/') or not (src.startswith('http://') or src.startswith('https://')):
                            from urllib.parse import urljoin
                            src = urljoin(url, src) 
                        
                        alt = img.get('alt', '')
                        
                        image_metadata.append({
                            "url": src,
                            "alt_text": alt,
                            "type": "picture_element",
                            "source_page": url
                        })
                
                # Extract background images from style attributes
                import re
                for element in elements_with_bg:
                    style = element.get('style', '')
                    # Use regex to find URLs in background-image styles
                    bg_urls = re.findall(r'background-image:.*?url\(["\']?([^"\']*)["\']?\)', style)
                    for bg_url in bg_urls:
                        if bg_url.startswith('/') or not (bg_url.startswith('http://') or bg_url.startswith('https://')):
                            from urllib.parse import urljoin
                            bg_url = urljoin(url, bg_url)

                        image_metadata.append({
                            "url": bg_url,
                            "type": "background_image",
                            "source_page": url
                        })
                
                # Remove duplicates and limit results
                unique_metadata = []
                seen_urls = set()
                for img_meta in image_metadata:
                    if img_meta["url"] not in seen_urls:
                        seen_urls.add(img_meta["url"])
                        unique_metadata.append(img_meta)
                        
                        # Apply limit per URL
                        if len(unique_metadata) >= limit_per_url:
                            break
                
                all_images.extend(unique_metadata)
                print(f"Extracted {len(unique_metadata)} images from {url}")
                
            except Exception as e:
                print(f"Error scraping images from {url}: {str(e)}")
    
    return all_images

def scrape_images_from_search_results(search_links: List[str], limit_per_url: int = 5, max_urls: int = 3) -> List[dict]:
    """
    Synchronous wrapper for async image scraper from search results.
    
    Args:
        search_links (List[str]): List of URLs to scrape images from
        limit_per_url (int): Maximum number of images to extract per URL
        max_urls (int): Maximum number of URLs to process
        
    Returns:
        List[Dict]: List of image metadata dictionaries
    """
    try:
        return asyncio.run(scrape_images_from_urls(search_links, limit_per_url, max_urls))
    except Exception as e:
        st.error(f"Error scraping images from search results: {str(e)}")
        return []

# Keep the remaining functions as they are
def extract_title_and_split_content(docs: List) -> Tuple[Optional[str], List]:
    """Extract title and split content into chunks."""
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
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP
    )
    content_chunks = text_splitter.split_documents(docs)
    print(f"Number of content chunks after splitting: {len(content_chunks)}")
    
    return title, content_chunks


def process_web(url: str) -> List:
    """Process web URL by loading document and splitting into chunks."""
    docs = load_web_document(url)
    if not docs:
        return []
    
    title, content_chunks = extract_title_and_split_content(docs)
    print(f"Title of the web document: {title}")  # Print statement
    return content_chunks

def process_image(file) -> List:
    """Process image file and add source metadata."""
    try:
        file_path = None
        # Determine file extension from the uploaded file name
        file_ext = os.path.splitext(file.name)[1].lower()
        
        # Create temporary file with appropriate extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(file.getvalue())
            file_path = tmp_file.name
            
        # Use the document processor to handle the image
        return prepare_document(file_path)
    except Exception as e:
        st.error(f"🖼️ Image processing error: {str(e)}")
        return []