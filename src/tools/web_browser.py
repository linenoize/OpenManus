import logging
import re
import json
import urllib.request
import urllib.parse
import urllib.error
from http.client import HTTPResponse
from typing import Dict, Any, Optional, List, Union

# Set up logging
logger = logging.getLogger(__name__)

class WebBrowserTool:
    """Tool for browsing and extracting data from web pages"""
    
    def __init__(self, 
                 user_agent: str = "OpenManus/1.0",
                 timeout: int = 30,
                 max_size: int = 10485760,  # 10MB
                 follow_redirects: bool = True,
                 max_redirects: int = 5):
        """
        Initialize the web browser tool.
        
        Args:
            user_agent: User agent string to use in requests
            timeout: Request timeout in seconds
            max_size: Maximum response size in bytes
            follow_redirects: Whether to follow redirects
            max_redirects: Maximum number of redirects to follow
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_size = max_size
        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects
        
        # Cache for storing already fetched URLs
        self.cache = {}
    
    def browse_web(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Browse a webpage and return its content and metadata.
        
        Args:
            url: The URL to browse
            params: Optional query parameters to add to the URL
            
        Returns:
            Dictionary with content and metadata
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                logger.error(f"Invalid URL: {url}")
                return {"error": f"Invalid URL: {url}"}
            
            # Add parameters to URL if provided
            if params:
                url_parts = list(urllib.parse.urlparse(url))
                query = dict(urllib.parse.parse_qsl(url_parts[4]))
                query.update(params)
                url_parts[4] = urllib.parse.urlencode(query)
                url = urllib.parse.urlunparse(url_parts)
            
            # Check cache
            if url in self.cache:
                logger.info(f"Using cached response for {url}")
                return self.cache[url]
            
            # Create request
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "close"
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            # Send request
            logger.info(f"Sending request to {url}")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                # Check response status
                if not self._is_valid_response(response):
                    logger.error(f"Invalid response from {url}: {response.status}")
                    return {"error": f"Request failed with status code {response.status}"}
                
                # Get content type
                content_type = response.getheader("Content-Type", "")
                
                # Read response (with size limit)
                content = response.read(self.max_size)
                
                # Process content based on type
                processed_content = self._process_content(content, content_type)
                
                # Get page metadata
                metadata = self._extract_metadata(response, processed_content)
                
                # Create result
                result = {
                    "url": url,
                    "status_code": response.status,
                    "content_type": content_type,
                    "content": processed_content,
                    "metadata": metadata
                }
                
                # Cache result
                self.cache[url] = result
                
                return result
                
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error while browsing {url}: {e.code} {e.reason}")
            return {
                "error": f"HTTP Error: {e.code} {e.reason}",
                "url": url
            }
        except urllib.error.URLError as e:
            logger.error(f"URL Error while browsing {url}: {e.reason}")
            return {
                "error": f"URL Error: {e.reason}",
                "url": url
            }
        except Exception as e:
            logger.error(f"Error browsing {url}: {str(e)}")
            return {
                "error": f"Error browsing URL: {str(e)}",
                "url": url
            }
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid."""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False
    
    def _is_valid_response(self, response: HTTPResponse) -> bool:
        """
        Check if a response is valid based on status code and content type.
        
        Args:
            response: HTTP response object
            
        Returns:
            True if response is valid, False otherwise
        """
        # Check status code
        if response.status < 200 or response.status >= 300:
            return False
        
        # Check content type (optional)
        content_type = response.getheader("Content-Type", "")
        if not content_type:
            return False
        
        return True
    
    def _process_content(self, content: bytes, content_type: str) -> str:
        """
        Process content based on content type.
        
        Args:
            content: Raw content bytes
            content_type: Content type header
            
        Returns:
            Processed content as string
        """
        # Handle HTML
        if "text/html" in content_type:
            return self._extract_text_from_html(content)
        
        # Handle JSON
        elif "application/json" in content_type:
            try:
                data = json.loads(content)
                return json.dumps(data, indent=2)
            except json.JSONDecodeError:
                return content.decode('utf-8', errors='replace')
        
        # Handle plain text
        elif "text/plain" in content_type:
            return content.decode('utf-8', errors='replace')
        
        # Other content types - return decoded text
        else:
            return content.decode('utf-8', errors='replace')
    
    def _extract_text_from_html(self, html_content: bytes) -> str:
        """
        Extract text from HTML content.
        
        Args:
            html_content: HTML content as bytes
            
        Returns:
            Extracted text as string
        """
        text = html_content.decode('utf-8', errors='replace')
        
        # Very basic HTML to text conversion with regex
        # In a real implementation, use a proper HTML parser like BeautifulSoup
        
        # Remove scripts and styles
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
        
        # Remove comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        
        # Handle special elements
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<hr\s*/?>', '\n---\n', text)
        text = re.sub(r'<li>', '\n- ', text)
        
        # Replace headings with marked up text
        text = re.sub(r'<h1.*?>(.*?)</h1>', r'\n# \1\n', text)
        text = re.sub(r'<h2.*?>(.*?)</h2>', r'\n## \1\n', text)
        text = re.sub(r'<h3.*?>(.*?)</h3>', r'\n### \1\n', text)
        text = re.sub(r'<h4.*?>(.*?)</h4>', r'\n#### \1\n', text)
        
        # Replace paragraph tags with newlines
        text = re.sub(r'<p.*?>', '\n', text)
        text = re.sub(r'</p>', '\n', text)
        
        # Replace div tags with newlines
        text = re.sub(r'<div.*?>', '\n', text)
        text = re.sub(r'</div>', '\n', text)
        
        # Remove all other tags
        text = re.sub(r'<.*?>', '', text)
        
        # Decode HTML entities
        text = self._decode_html_entities(text)
        
        # Normalize whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _decode_html_entities(self, text: str) -> str:
        """
        Decode common HTML entities.
        
        Args:
            text: Text with HTML entities
            
        Returns:
            Text with decoded entities
        """
        entities = {
            '&nbsp;': ' ',
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
            '&quot;': '"',
            '&apos;': "'",
            '&#39;': "'",
            '&mdash;': '—',
            '&ndash;': '–',
            '&hellip;': '…'
        }
        
        for entity, char in entities.items():
            text = text.replace(entity, char)
            
        # Handle numeric entities
        text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
        
        return text
    
    def _extract_metadata(self, response: HTTPResponse, content: str) -> Dict[str, Any]:
        """
        Extract metadata from response and content.
        
        Args:
            response: HTTP response object
            content: Processed content
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            "headers": {k: v for k, v in response.getheaders()},
            "length": len(content),
            "encoding": response.headers.get_content_charset('utf-8')
        }
        
        # Try to extract title (very basic approach)
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        # Try to extract meta description
        desc_match = re.search(r'<meta[^>]*name=["\'](description|og:description)["\'][^>]*content=["\'](.*?)["\']', 
                            content, re.IGNORECASE)
        if desc_match:
            metadata["description"] = desc_match.group(2).strip()
        
        return metadata
    
    def search(self, query: str, search_engine: str = "default") -> Dict[str, Any]:
        """
        Perform a web search using a search engine.
        
        Args:
            query: Search query
            search_engine: Search engine to use
            
        Returns:
            Dictionary with search results
        """
        # This is a simplified implementation
        # In a real implementation, this would use proper search engine APIs
        
        # Encode query
        encoded_query = urllib.parse.quote_plus(query)
        
        # Determine search URL
        if search_engine == "google":
            url = f"https://www.google.com/search?q={encoded_query}"
        elif search_engine == "bing":
            url = f"https://www.bing.com/search?q={encoded_query}"
        else:  # default
            url = f"https://www.google.com/search?q={encoded_query}"
        
        # Browse search results page
        result = self.browse_web(url)
        
        # Parse search results (this is a placeholder)
        # In a real implementation, this would parse the search results page
        if "error" in result:
            return result
            
        return {
            "query": query,
            "search_engine": search_engine,
            "url": url,
            "content": result.get("content", ""),
            "note": "Search functionality is simplified. Use a search API for better results."
        }
        
    def download_file(self, url: str, max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Download a file from a URL.
        
        Args:
            url: URL to download
            max_size: Maximum file size in bytes
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                logger.error(f"Invalid URL: {url}")
                return {"error": f"Invalid URL: {url}"}
            
            # Set max size
            if max_size is None:
                max_size = self.max_size
            
            # Create request
            headers = {
                "User-Agent": self.user_agent,
                "Connection": "close"
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            # Send request
            logger.info(f"Downloading file from {url}")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                # Check response status
                if response.status < 200 or response.status >= 300:
                    logger.error(f"Invalid response from {url}: {response.status}")
                    return {"error": f"Download failed with status code {response.status}"}
                
                # Get content type
                content_type = response.getheader("Content-Type", "")
                
                # Get filename from content-disposition header or URL
                filename = self._get_filename(response, url)
                
                # Read file content
                content = response.read(max_size)
                
                return {
                    "url": url,
                    "status_code": response.status,
                    "content_type": content_type,
                    "filename": filename,
                    "content": content,
                    "size": len(content)
                }
                
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error while downloading {url}: {e.code} {e.reason}")
            return {
                "error": f"HTTP Error: {e.code} {e.reason}",
                "url": url
            }
        except urllib.error.URLError as e:
            logger.error(f"URL Error while downloading {url}: {e.reason}")
            return {
                "error": f"URL Error: {e.reason}",
                "url": url
            }
        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            return {
                "error": f"Error downloading file: {str(e)}",
                "url": url
            }
    
    def _get_filename(self, response: HTTPResponse, url: str) -> str:
        """
        Get filename from response headers or URL.
        
        Args:
            response: HTTP response object
            url: URL
            
        Returns:
            Filename
        """
        # Try to get filename from content-disposition header
        content_disposition = response.getheader("Content-Disposition", "")
        if content_disposition:
            match = re.search(r'filename=["\'](.*?)["\']', content_disposition)
            if match:
                return match.group(1)
        
        # Fall back to URL path
        path = urllib.parse.urlparse(url).path
        return os.path.basename(path) or "downloaded_file"