from google import genai
from google.genai import types
from typing import List, Tuple, Dict, Optional
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
from urllib.parse import urlparse, parse_qs, unquote
import traceback

def google_search(query: str) -> Tuple[str, List[str]]:
    """
    Perform a Google search using Gemini's built-in search capability.
    Returns a tuple containing (text_response, search_links)
    """
    try:
        client = genai.Client(api_key='AIzaSyAqA979bDpQE6j0cHZ1tOBzVwZ3gq9FzeA')
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0.2,
                tools=[types.Tool(
                    google_search=types.GoogleSearchRetrieval()
                )]
            )
        )
        
        # Extract links from citations and grounding metadata
        links = []
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                # Extract links from citation metadata
                if hasattr(candidate, 'citation_metadata') and candidate.citation_metadata:
                    for citation in candidate.citation_metadata.citations:
                        if hasattr(citation, 'url') and citation.url:
                            links.append(citation.url)
                # Extract links from grounding metadata
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    for chunk in candidate.grounding_metadata.grounding_chunks:
                        if hasattr(chunk, 'web') and chunk.web:
                            links.append(chunk.web.uri)
        
        # Log response details to console
        print("===== GOOGLE SEARCH RESPONSE =====")
        print(f"Query: {query}")
        print(f"Response text: {response.text}")
        print(f"Found {len(links)} links:")
        for i, link in enumerate(links):
            print(f"  {i+1}. {link}")
        print("=================================")
                            
        return response.text, links
    except Exception as e:
        print(f"ERROR: Google search failed: {str(e)}")
        st.error(f"🔍 Google search error: {str(e)}")
        return "", []

def extract_urls_from_response(response_text: str) -> List[str]:
    """
    Extract URLs from a text response that may not be properly formatted as JSON.
    This is a fallback method for when the standard JSON parsing fails.
    
    Args:
        response_text (str): Raw text response from the API
        
    Returns:
        List[str]: List of extracted URLs
    """
    try:
        # Try to find any URLs in the text using regex
        url_pattern = r'https?://[^\s()<>"\']+'
        found_urls = re.findall(url_pattern, response_text)
        
        # Filter out URLs that don't seem like valid web links
        valid_urls = []
        for url in found_urls:
            # Remove trailing punctuation that might have been captured
            while url and url[-1] in '.,;:!?)]}\'\"':
                url = url[:-1]
                
            # Basic validation that this looks like a URL
            if len(url) > 10 and '.' in url:
                valid_urls.append(url)
                
        print(f"Extracted {len(valid_urls)} URLs using regex from response")
        return valid_urls
    except Exception as e:
        print(f"Error extracting URLs with regex: {str(e)}")
        return []

def enhanced_google_search(query: str) -> Tuple[str, List[str]]:
    """
    Enhanced version of Google search that handles errors better and includes
    fallback mechanisms for extracting URLs from responses.
    
    Args:
        query (str): The search query
        
    Returns:
        Tuple[str, List[str]]: Tuple containing (text_response, search_links)
    """
    try:
        # First try the standard Google search
        text_response, links = google_search(query)
        
        # If no links were found but we have text, try to extract URLs from the text
        if not links and text_response:
            print("No links found via standard extraction, trying regex fallback")
            fallback_links = extract_urls_from_response(text_response)
            if fallback_links:
                links = fallback_links
                print(f"Fallback extraction found {len(links)} links")
        
        return text_response, links
    except Exception as e:
        error_msg = f"Enhanced Google search failed: {str(e)}"
        print(f"ERROR: {error_msg}")
        if 'st' in globals() and hasattr(st, 'session_state'):
            st.error(f"🔍 {error_msg}")
        return "", []

def fetch_image_with_direct_api(query: str) -> List[Dict[str, str]]:
    """
    Use Gemini's image-generating capabilities to fetch relevant images
    as a fallback when web scraping fails to find useful images.
    
    Args:
        query (str): Search query to find images for
        
    Returns:
        List[Dict[str, str]]: List of dictionaries containing image information
    """
    try:
        # Handle API key retrieval for both Streamlit and FastAPI environments
        api_key = None
        if 'st' in globals() and hasattr(st, 'session_state'):
            # Streamlit environment
            api_key = st.session_state.get("google_api_key", None)
        
        # Fallback to environment variable if not in session
        if not api_key:
            import os
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            
        if not api_key:
            print("No API key available for direct image search")
            return []
            
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        
        # Construct a prompt asking for image links relevant to the query
        image_query_prompt = f"""
        Find and provide links to 3-5 relevant, high-quality images for the search query: "{query}"
        
        For each image, provide:
        1. The full direct image URL (must end with .jpg, .jpeg, .png, .gif, or .webp)
        2. The source webpage URL
        3. A brief description of what the image shows
        
        Format your response as a list of JSON objects, like this:
        [
          {{
            "image_url": "https://example.com/image.jpg",
            "source_page": "https://example.com/article",
            "description": "Brief description of the image content"
          }},
          ...more images...
        ]
        
        Make sure all image URLs are direct links to image files, not webpage URLs.
        """
        
        # Call the model to get image suggestions
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=image_query_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        # Parse the response
        try:
            results = []
            # Try to parse as valid JSON
            if hasattr(response, 'text') and response.text:
                try:
                    json_response = json.loads(response.text)
                    if isinstance(json_response, list):
                        for item in json_response:
                            if isinstance(item, dict) and 'image_url' in item:
                                # Validate image URL
                                if re.search(r'\.(jpg|jpeg|png|gif|webp)(\?.*)?$', item['image_url'], re.IGNORECASE):
                                    results.append({
                                        "image_url": item['image_url'],
                                        "source_page": item.get('source_page', "Direct API search"),
                                        "description": item.get('description', "")
                                    })
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract URLs using regex
                    print("Response not valid JSON, trying to extract image URLs with regex")
                    image_url_pattern = r'https?://[^\s()<>]+\.(jpg|jpeg|png|gif|webp)(\?[^\s<>]*)?'
                    image_urls = re.findall(image_url_pattern, response.text, re.IGNORECASE)
                    for i, (url_part, _) in enumerate(image_urls[:5]):
                        results.append({
                            "image_url": url_part,
                            "source_page": "Direct API search",
                            "description": f"Image {i+1} for {query}"
                        })
            
            print(f"Direct API search found {len(results)} images")
            return results
        except Exception as e:
            print(f"Error parsing direct image search response: {str(e)}")
            return []
    except Exception as e:
        print(f"Direct image search failed: {str(e)}")
        return []

def get_images_for_query(query: str, max_images: int = 10) -> List[Dict[str, str]]:
    """
    Comprehensive function to get images for a query using multiple methods.
    First tries web search + scraping, then falls back to direct API search if needed.
    
    Args:
        query (str): The search query
        max_images (int): Maximum number of images to return
        
    Returns:
        List[Dict[str, str]]: List of dictionaries with image URLs and metadata
    """
    try:
        # Step 1: Try enhanced Google search to get links
        print(f"Searching for images related to: {query}")
        text_response, links = enhanced_google_search(query)
        
        if not links:
            print("No links found from search, trying direct API")
            # Step 2: If no links, try direct API approach
            return fetch_image_with_direct_api(query)
        
        # Step 3: Try to scrape images from the links
        images = scrape_images_from_links(links, total_max_images=max_images)
        
        # Step 4: If scraping didn't yield enough results, supplement with direct API
        if len(images) < 3:
            print(f"Only found {len(images)} images via scraping, adding direct API results")
            direct_images = fetch_image_with_direct_api(query)
            
            # Add unique images from direct API search
            for img in direct_images:
                if len(images) >= max_images:
                    break
                    
                # Check if this image URL is already in our results
                if not any(existing['image_url'] == img['image_url'] for existing in images):
                    images.append(img)
        
        print(f"Final image count: {len(images)}")
        return images[:max_images]
    except Exception as e:
        print(f"Error in get_images_for_query: {str(e)}")
        traceback.print_exc()
        return []

def scrape_images_from_links(links: List[str], max_images_per_link: int = 5, total_max_images: int = 20) -> List[Dict[str, str]]:
    """
    Scrape image URLs from a list of web links.
    
    Args:
        links (List[str]): List of URLs to scrape for images
        max_images_per_link (int): Maximum number of images to extract from each link
        total_max_images (int): Maximum total number of images to return
        
    Returns:
        List[Dict[str, str]]: List of dictionaries containing image URLs and their source pages
                             [{"image_url": "https://...", "source_page": "https://..."}]
    """
    if not links:
        print("No links provided for image scraping")
        return []
    
    # Only process the top 3 links to improve performance
    links_to_process = links[:3]
    print(f"Scraping images from top {len(links_to_process)} links")
    
    def resolve_redirect_url(url: str) -> str:
        """Resolve Google Search API redirect URLs to their actual destinations"""
        try:
            # Check if this is a Google Vertex Search redirect URL
            if "vertexaisearch.cloud.google.com/grounding-api-redirect" in url:
                # Try to follow the redirect with a HEAD request first to get the destination
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
                if response.url != url:
                    print(f"Resolved redirect: {url} -> {response.url}")
                    return response.url
                
                # If HEAD request doesn't resolve, try a full GET request
                response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                if response.url != url:
                    print(f"Resolved redirect with GET: {url} -> {response.url}")
                    return response.url
                
                print(f"Unable to resolve redirect URL: {url}")
            return url
        except Exception as e:
            print(f"Error resolving redirect URL {url}: {str(e)}")
            return url

    def extract_images_from_url(url: str) -> List[Dict[str, str]]:
        """Helper function to extract images from a single URL"""
        images = []
        try:
            # Resolve redirect URL first
            resolved_url = resolve_redirect_url(url)
            
            # Add headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            # Print details for debugging
            print(f"Requesting URL: {resolved_url}")
            response = requests.get(resolved_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '')
            print(f"Content-Type: {content_type}")
            
            # Skip if not HTML content
            if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                print(f"Skipping non-HTML content: {content_type}")
                return images
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract OpenGraph image first (usually high quality and relevant)
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                img_url = og_image.get('content')
                if img_url:
                    # Convert relative URL to absolute if necessary
                    if not img_url.startswith(('http://', 'https://')):
                        base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(resolved_url))
                        if img_url.startswith('/'):
                            img_url = base_url + img_url
                        else:
                            img_url = base_url + '/' + img_url
                    
                    images.append({"image_url": img_url, "source_page": resolved_url})
                    print(f"Found OpenGraph image: {img_url}")
            
            # Twitter card image (another good source)
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content') and len(images) < max_images_per_link:
                img_url = twitter_image.get('content')
                if img_url and not any(img['image_url'] == img_url for img in images):
                    # Convert relative URL to absolute if necessary
                    if not img_url.startswith(('http://', 'https://')):
                        base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(resolved_url))
                        if img_url.startswith('/'):
                            img_url = base_url + img_url
                        else:
                            img_url = base_url + '/' + img_url
                    
                    images.append({"image_url": img_url, "source_page": resolved_url})
                    print(f"Found Twitter card image: {img_url}")
            
            # Find all img tags if we still need more images
            if len(images) < max_images_per_link:
                img_tags = soup.find_all('img')
                print(f"Found {len(img_tags)} img tags on page")
                
                # Extract and filter image URLs
                for img in img_tags:
                    if len(images) >= max_images_per_link:
                        break
                    
                    # Try different attributes where image URLs might be stored
                    img_url = None
                    for attr in ['src', 'data-src', 'data-original', 'data-lazy-src', 'data-srcset']:
                        img_url = img.get(attr)
                        if img_url:
                            break
                    
                    if not img_url:
                        continue
                    
                    # If we have srcset, take the largest image
                    if attr == 'data-srcset' or img.get('srcset'):
                        srcset = img.get('srcset') or img_url
                        try:
                            # Parse srcset to get the highest resolution image
                            largest_img = None
                            largest_width = 0
                            
                            for src_item in srcset.split(','):
                                parts = src_item.strip().split(' ')
                                if len(parts) >= 2:
                                    # Extract the URL and width value
                                    src = parts[0].strip()
                                    width_str = parts[1].strip()
                                    if width_str.endswith('w'):
                                        try:
                                            width = int(width_str[:-1])
                                            if width > largest_width:
                                                largest_width = width
                                                largest_img = src
                                        except ValueError:
                                            pass
                            
                            if largest_img:
                                img_url = largest_img
                        except Exception as e:
                            print(f"Error parsing srcset: {str(e)}")
                    
                    # Skip data URLs (base64 encoded images)
                    if img_url.startswith('data:'):
                        continue
                    
                    # Convert relative URLs to absolute URLs
                    if img_url.startswith('//'):
                        # Protocol-relative URL
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        # Root-relative URL
                        base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(resolved_url))
                        img_url = base_url + img_url
                    elif not img_url.startswith(('http://', 'https://')):
                        # Path-relative URL
                        base_uri = urlparse(resolved_url)
                        base_url = f"{base_uri.scheme}://{base_uri.netloc}"
                        path = "/".join(base_uri.path.split('/')[:-1]) if '/' in base_uri.path else ""
                        if path and not path.endswith('/'):
                            path += '/'
                        img_url = base_url + path + img_url
                    
                    # Filter out small images, icons, and non-image files
                    # Include additional image extensions and ignore common exclusion patterns
                    if (re.search(r'\.(jpg|jpeg|png|gif|webp|bmp|tiff)(\?.*)?$', img_url, re.IGNORECASE) and
                        not re.search(r'(icon|favicon|logo-small|button|bullet|pixel|1x1|spinner|loading)', img_url.lower())):
                        
                        # Check image dimensions if available
                        width = img.get('width')
                        height = img.get('height')
                        has_good_size = False
                        
                        if width and height:
                            try:
                                width_val = int(width)
                                height_val = int(height)
                                # Only include reasonably sized images
                                if width_val >= 200 and height_val >= 200:
                                    has_good_size = True
                            except ValueError:
                                # Non-numeric dimensions, include it anyway
                                has_good_size = True
                        else:
                            # No dimensions specified, include it
                            has_good_size = True
                        
                        if has_good_size and not any(img['image_url'] == img_url for img in images):
                            images.append({"image_url": img_url, "source_page": resolved_url})
                            print(f"Added image: {img_url}")
            
            print(f"Extracted {len(images)} images from {resolved_url}")
            return images
            
        except Exception as e:
            print(f"Error scraping images from {url}: {str(e)}")
            return []
    
    # Process each link sequentially instead of using ThreadPoolExecutor
    # This can help with debugging and avoid overwhelming the target servers
    all_images = []
    for url in links_to_process:
        try:
            print(f"Processing {url}")
            images = extract_images_from_url(url)
            all_images.extend(images)
            
            # Break early if we've collected enough images
            if len(all_images) >= total_max_images:
                break
        except Exception as e:
            print(f"Failed to process {url}: {str(e)}")
    
    # Log results
    print(f"===== IMAGE SCRAPING RESULTS =====")
    print(f"Scraped {len(all_images)} images from {len(links_to_process)} links")
    for i, img in enumerate(all_images[:total_max_images]):
        print(f"  {i+1}. {img['image_url']} (from {img['source_page']})")
    print("=================================")
    
    return all_images[:total_max_images]