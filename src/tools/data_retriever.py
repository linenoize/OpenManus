import os
import json
import logging
import re
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class DataRetrieverTool:
    """Tool for retrieving data from various sources including memory store, APIs, and databases."""
    
    def __init__(self, 
                memory_path: str = "data/memory",
                cache_dir: str = "data/metadata_cache",
                vector_search_enabled: bool = True):
        """
        Initialize the data retriever tool.
        
        Args:
            memory_path: Path to memory storage directory
            cache_dir: Directory for caching API results
            vector_search_enabled: Whether to use vector-based search when available
        """
        self.memory_path = memory_path
        self.cache_dir = cache_dir
        self.vector_search_enabled = vector_search_enabled
        
        # Create directories if they don't exist
        os.makedirs(self.memory_path, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize cache for API results
        self.api_cache = self._load_api_cache()
        
        # Initialize data sources
        self.data_sources = self._initialize_data_sources()
        
        # Try to import vector database for semantic search
        try:
            from src.tools.vector_db_tool import VectorDBTool
            self.vector_db = VectorDBTool(base_path="data/vectors")
            logger.info("Vector database initialized for semantic search")
        except Exception as e:
            logger.warning(f"Vector database not available: {e}")
            self.vector_db = None
            self.vector_search_enabled = False
    
    def _initialize_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize available data sources.
        
        Returns:
            Dictionary with data source configurations
        """
        sources = {
            "memory": {
                "type": "internal",
                "enabled": True,
                "description": "Local memory storage",
                "search_method": self.search_memory
            },
            "local_files": {
                "type": "filesystem",
                "enabled": True,
                "description": "Local file system",
                "search_method": self.search_local_files
            }
        }
        
        # Additional data sources could be added here, like:
        # - Database connections
        # - API integrations
        # - External search services
        
        return sources
    
    def _load_api_cache(self) -> Dict[str, Dict[str, Any]]:
        """
        Load API cache from file.
        
        Returns:
            Dictionary with cached API results
        """
        cache_file = os.path.join(self.cache_dir, "api_cache.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                    
                # Filter out expired entries
                now = time.time()
                filtered_cache = {}
                for key, entry in cache.items():
                    if entry.get("expires_at", 0) > now:
                        filtered_cache[key] = entry
                
                return filtered_cache
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Error loading API cache: {e}")
                return {}
        else:
            return {}
    
    def _save_api_cache(self) -> None:
        """Save API cache to file."""
        cache_file = os.path.join(self.cache_dir, "api_cache.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.api_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving API cache: {e}")
    
    def _cache_api_result(self, key: str, data: Any, ttl: int = 3600) -> None:
        """
        Cache API result with expiration.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.api_cache[key] = {
            "data": data,
            "cached_at": time.time(),
            "expires_at": time.time() + ttl
        }
        
        # Save to file
        self._save_api_cache()
    
    def _get_cached_api_result(self, key: str) -> Optional[Any]:
        """
        Get cached API result if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data if available and not expired, None otherwise
        """
        if key in self.api_cache:
            entry = self.api_cache[key]
            if entry.get("expires_at", 0) > time.time():
                return entry.get("data")
        
        return None
    
    def retrieve_data(self, query: str, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Retrieve data from specified sources based on query.
        
        Args:
            query: The search query
            sources: List of source names to search (None for all available)
            
        Returns:
            Dictionary with results from each source
        """
        # Track execution time
        start_time = time.time()
        
        # Determine sources to search
        if sources is None:
            # Use all enabled sources
            sources_to_search = {name: config for name, config in self.data_sources.items() 
                               if config.get("enabled", False)}
        else:
            # Use only specified sources
            sources_to_search = {name: config for name, config in self.data_sources.items() 
                               if name in sources and config.get("enabled", False)}
        
        if not sources_to_search:
            logger.warning(f"No valid data sources specified: {sources}")
            return {
                "error": "No valid data sources specified",
                "available_sources": list(self.data_sources.keys())
            }
        
        # Search each source
        results = {}
        for source_name, source_config in sources_to_search.items():
            try:
                if "search_method" in source_config and callable(source_config["search_method"]):
                    search_method = source_config["search_method"]
                    source_results = search_method(query)
                    results[source_name] = source_results
                else:
                    logger.warning(f"No search method defined for source: {source_name}")
                    results[source_name] = {"error": "No search method defined"}
            except Exception as e:
                logger.error(f"Error searching {source_name}: {str(e)}")
                results[source_name] = {"error": f"Search error: {str(e)}"}
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        return {
            "query": query,
            "sources": list(sources_to_search.keys()),
            "results": results,
            "execution_time": execution_time
        }
    
    def search_memory(self, query: str, namespace: str = "general") -> Dict[str, Any]:
        """
        Search through stored memories using text matching or vector search.
        
        Args:
            query: The search query
            namespace: The memory namespace to search in
            
        Returns:
            Dictionary with search results
        """
        try:
            # Try vector search if enabled and available
            if self.vector_search_enabled and self.vector_db:
                try:
                    collection_name = f"memory_{namespace}"
                    if collection_name in self.vector_db.list_collections():
                        # Use vector search
                        vector_results = self.vector_db.search(
                            collection_name=collection_name,
                            query=query,
                            k=5
                        )
                        
                        if vector_results:
                            # Get parent memories for these chunks
                            parent_ids = set(result.get("metadata", {}).get("parent_id") 
                                          for result in vector_results 
                                          if "metadata" in result and "parent_id" in result["metadata"])
                            
                            memories = self.get_memories(namespace)
                            matched_memories = [memory for memory in memories 
                                             if memory.get("id") in parent_ids]
                            
                            return {
                                "source": "vector_search",
                                "query": query,
                                "namespace": namespace,
                                "match_count": len(matched_memories),
                                "results": matched_memories
                            }
                except Exception as e:
                    logger.warning(f"Vector search failed, falling back to text search: {e}")
            
            # Fallback to simple text matching
            memories = self.get_memories(namespace)
            
            matched_memories = []
            query_lower = query.lower()
            
            for memory in memories:
                content = memory.get("content", "").lower()
                if query_lower in content:
                    # Calculate simple relevance score
                    score = content.count(query_lower) / max(1, len(content))
                    memory_result = memory.copy()
                    memory_result["relevance_score"] = score
                    matched_memories.append(memory_result)
            
            # Sort by relevance
            matched_memories.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            return {
                "source": "text_search",
                "query": query,
                "namespace": namespace,
                "match_count": len(matched_memories),
                "results": matched_memories
            }
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return {"error": f"Memory search error: {str(e)}"}
    
    def search_local_files(self, query: str, base_path: str = "data/files/local") -> Dict[str, Any]:
        """
        Search local files for content matching query.
        
        Args:
            query: The search query
            base_path: Base directory to search in
            
        Returns:
            Dictionary with search results
        """
        try:
            if not os.path.exists(base_path) or not os.path.isdir(base_path):
                return {
                    "error": f"Base path not found: {base_path}",
                    "query": query
                }
            
            results = []
            
            # Create regex pattern for search
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            
            # Search files in directory
            for root, _, files in os.walk(base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip binary and very large files
                    if self._is_text_file(file_path) and os.path.getsize(file_path) < 1024 * 1024:  # 1MB max
                        try:
                            # Search file content
                            with open(file_path, 'r', errors='ignore') as f:
                                content = f.read()
                                
                                matches = pattern.findall(content)
                                if matches:
                                    # Create result with context
                                    rel_path = os.path.relpath(file_path, base_path)
                                    
                                    # Get context for first match
                                    match_context = self._get_context(content, matches[0], 100)
                                    
                                    results.append({
                                        "file": rel_path,
                                        "matches": len(matches),
                                        "context": match_context,
                                        "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                                    })
                        except Exception as e:
                            logger.warning(f"Error searching file {file_path}: {e}")
            
            # Sort by number of matches
            results.sort(key=lambda x: x.get("matches", 0), reverse=True)
            
            return {
                "query": query,
                "base_path": base_path,
                "match_count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Error searching local files: {str(e)}")
            return {"error": f"File search error: {str(e)}"}
    
    def _is_text_file(self, file_path: str) -> bool:
        """
        Check if a file is a text file based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is likely a text file, False otherwise
        """
        # Common text file extensions
        text_extensions = {
            '.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm', '.css', '.js', 
            '.py', '.java', '.c', '.cpp', '.h', '.sh', '.log', '.cfg', '.conf', '.ini'
        }
        
        _, ext = os.path.splitext(file_path.lower())
        return ext in text_extensions
    
    def _get_context(self, content: str, match: str, context_size: int) -> str:
        """
        Get context around a match in content.
        
        Args:
            content: The full content string
            match: The matched text
            context_size: Number of characters for context
            
        Returns:
            String with context around match
        """
        match_pos = content.lower().find(match.lower())
        if match_pos == -1:
            return ""
            
        start = max(0, match_pos - context_size)
        end = min(len(content), match_pos + len(match) + context_size)
        
        # Find line boundaries
        if start > 0:
            # Find start of the line
            line_start = content.rfind('\n', 0, start)
            if line_start != -1:
                start = line_start + 1
                
        if end < len(content):
            # Find end of the line
            line_end = content.find('\n', end)
            if line_end != -1:
                end = line_end
        
        context = content[start:end]
        if start > 0:
            context = "..." + context
        if end < len(content):
            context = context + "..."
            
        return context
    
    def get_memories(self, namespace: str = "general") -> List[Dict[str, Any]]:
        """
        Retrieve all memories from a namespace.
        
        Args:
            namespace: The memory namespace to retrieve from
            
        Returns:
            List of memory entries
        """
        memory_file = os.path.join(self.memory_path, f"{namespace}.json")
        
        if not os.path.exists(memory_file):
            return []
            
        try:
            with open(memory_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading memories: {e}")
            return []
    
    def get_memory_by_id(self, memory_id: str, namespace: str = "general") -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            namespace: The namespace to search in
            
        Returns:
            The memory if found, None otherwise
        """
        memories = self.get_memories(namespace)
        
        for memory in memories:
            if memory.get("id") == memory_id:
                return memory
                
        return None
    
    def list_memory_namespaces(self) -> List[str]:
        """
        List all available memory namespaces.
        
        Returns:
            List of namespace names
        """
        if not os.path.exists(self.memory_path):
            return []
            
        namespaces = []
        for filename in os.listdir(self.memory_path):
            if filename.endswith(".json"):
                namespaces.append(filename[:-5])  # Remove .json extension
                
        return namespaces
    
    def search_api(self, 
                  api_name: str, 
                  query: str, 
                  params: Optional[Dict[str, Any]] = None,
                  use_cache: bool = True,
                  cache_ttl: int = 3600) -> Dict[str, Any]:
        """
        Search using a configured API.
        
        Args:
            api_name: Name of the API to use
            query: Search query
            params: Additional API parameters
            use_cache: Whether to use cached results
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            Dictionary with API response
        """
        # This is a simplified API search implementation
        # In a real implementation, there would be proper API clients and configuration
        
        if params is None:
            params = {}
        
        # Create cache key from API name, query, and params
        cache_key = f"{api_name}:{query}:{json.dumps(params, sort_keys=True)}"
        
        # Check cache if enabled
        if use_cache:
            cached_result = self._get_cached_api_result(cache_key)
            if cached_result:
                logger.info(f"Using cached result for API: {api_name}")
                cached_result["cached"] = True
                return cached_result
        
        # Placeholder for API implementations
        if api_name == "wikipedia":
            result = self._search_wikipedia(query, params)
        elif api_name == "weather":
            result = self._search_weather(query, params)
        else:
            return {
                "error": f"Unknown API: {api_name}",
                "available_apis": ["wikipedia", "weather"]
            }
        
        # Cache result if successful
        if "error" not in result and use_cache:
            self._cache_api_result(cache_key, result, cache_ttl)
        
        return result
    
    def _search_wikipedia(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search Wikipedia (placeholder implementation).
        
        Args:
            query: Search query
            params: Additional parameters
            
        Returns:
            Dictionary with search results
        """
        # This is a placeholder - in a real implementation, use a proper API client
        return {
            "api": "wikipedia",
            "query": query,
            "params": params,
            "results": [
                {
                    "title": f"Wikipedia article about {query}",
                    "snippet": f"This is a placeholder for Wikipedia results about {query}.",
                    "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
                }
            ],
            "note": "This is a placeholder implementation. Install wikipedia package for real API access."
        }
    
    def _search_weather(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get weather information (placeholder implementation).
        
        Args:
            query: Location query
            params: Additional parameters
            
        Returns:
            Dictionary with weather information
        """
        # This is a placeholder - in a real implementation, use a proper weather API
        return {
            "api": "weather",
            "location": query,
            "params": params,
            "forecast": {
                "current": {
                    "temperature": "Unknown",
                    "conditions": "Unknown",
                    "humidity": "Unknown"
                }
            },
            "note": "This is a placeholder implementation. Configure a real weather API for actual data."
        }