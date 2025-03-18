import os
import json
import nltk
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import textwrap
from collections import defaultdict

# Set nltk data path to look in system directory first
nltk.data.path = ['/usr/local/share/nltk_data'] + nltk.data.path

try:
    # Use pre-downloaded punkt tokenizer
    from nltk.tokenize import sent_tokenize
except ImportError:
    # Fallback to a simple split method if nltk is not available
    def sent_tokenize(text):
        return text.split('. ')

# Import VectorDBTool for semantic search capabilities
from src.tools.vector_db_tool import VectorDBTool

class MemoryTool:
    """
    Tool for storing and retrieving information across sessions.
    Provides persistent memory capabilities to the agent system.
    
    Features:
    - JSON-based file storage organized by namespaces
    - Vector embeddings for semantic search (optional)
    - Automatic memory chunking for long texts
    - Relevance scoring for search results
    """
    
    def __init__(self, 
                 memory_path: str = "data/memory", 
                 use_vectors: bool = True,
                 vector_db_path: str = "data/memory_vectors",
                 model_name: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 512,
                 chunk_overlap: int = 50):
        """
        Initialize the memory tool.
        
        Args:
            memory_path: Path to store memory files
            use_vectors: Whether to use vector embeddings for semantic search
            vector_db_path: Path to store vector database
            model_name: Name of the embedding model to use
            chunk_size: Maximum size of text chunks for vectorization
            chunk_overlap: Overlap between chunks to maintain context
        """
        self.memory_path = memory_path
        self.use_vectors = use_vectors
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Ensure memory directory exists
        os.makedirs(self.memory_path, exist_ok=True)
        
        # Initialize vector database if enabled
        self.vector_db = None
        if self.use_vectors:
            try:
                self.vector_db = VectorDBTool(
                    base_path=vector_db_path,
                    model_name=model_name
                )
                print(f"Vector-based memory enabled with model: {model_name}")
            except Exception as e:
                print(f"Warning: Could not initialize vector database: {e}")
                print("Falling back to text-based search")
                self.use_vectors = False
    
    def store(self, content: str, metadata: Optional[Dict[str, Any]] = None, 
              namespace: str = "general", memory_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Store a memory with optional metadata.
        
        Args:
            content: The content to store
            metadata: Optional metadata associated with this memory
            namespace: The namespace to store this memory in
            memory_id: Optional ID for the memory. If None, a timestamp will be used
            
        Returns:
            The memory entry that was stored
        """
        # Get existing memories
        memories = self.get_all(namespace)
        
        # Create memory object
        memory_id = memory_id or datetime.now().isoformat()
        
        memory = {
            "id": memory_id,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Add to memories list
        memories.append(memory)
        
        # Write back to file
        self._save_memories(memories, namespace)
        
        # Store in vector database if enabled
        if self.use_vectors and self.vector_db:
            # Create or ensure the collection exists
            collection_name = f"memory_{namespace}"
            if collection_name not in self.vector_db.list_collections():
                self.vector_db.create_collection(collection_name)
                
            # Split long content into chunks for better semantic search
            chunks = self._chunk_text(content)
            
            # Add metadata about chunk and parent memory
            chunk_metadatas = []
            for i, _ in enumerate(chunks):
                chunk_metadata = {
                    "parent_id": memory_id,
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                    **metadata
                } if metadata else {
                    "parent_id": memory_id,
                    "chunk_index": i,
                    "chunk_count": len(chunks)
                }
                chunk_metadatas.append(chunk_metadata)
                
            # Store chunks in vector database
            self.vector_db.add_texts(
                collection_name=collection_name,
                texts=chunks,
                metadatas=chunk_metadatas,
                external_ids=[f"{memory_id}_chunk_{i}" for i in range(len(chunks))]
            )
        
        return memory
    
    def get(self, memory_id: str, namespace: str = "general") -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            namespace: The namespace to search in
            
        Returns:
            The memory entry if found, None otherwise
        """
        memories = self.get_all(namespace)
        
        for memory in memories:
            if memory.get("id") == memory_id:
                return memory
                
        return None
    
    def get_all(self, namespace: str = "general") -> List[Dict[str, Any]]:
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
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def search(self, query: str, namespace: str = "general", 
               k: int = 5, min_score: float = 0.0,
               use_vectors: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Search through stored memories for relevant information.
        
        Args:
            query: The search query
            namespace: The memory namespace to search in
            k: Maximum number of results to return
            min_score: Minimum similarity score (0-1) for results
            use_vectors: Whether to use vector search. If None, use instance default.
            
        Returns:
            List of matching memory entries with relevance scores
        """
        # Determine search method
        use_vectors = self.use_vectors if use_vectors is None else use_vectors
        
        if use_vectors and self.vector_db:
            return self._vector_search(query, namespace, k, min_score)
        else:
            return self._text_search(query, namespace)
    
    def update(self, memory_id: str, content: Optional[str] = None, 
               metadata: Optional[Dict[str, Any]] = None, namespace: str = "general") -> Optional[Dict[str, Any]]:
        """
        Update an existing memory.
        
        Args:
            memory_id: The ID of the memory to update
            content: New content (if None, content won't be updated)
            metadata: New metadata (if None, metadata won't be updated)
            namespace: The namespace where the memory is stored
            
        Returns:
            The updated memory entry if found and updated, None otherwise
        """
        memories = self.get_all(namespace)
        
        # Find and update the memory
        for i, memory in enumerate(memories):
            if memory.get("id") == memory_id:
                old_content = memory["content"]
                
                if content is not None:
                    memory["content"] = content
                
                if metadata is not None:
                    # Update metadata by merging with existing
                    memory["metadata"] = {**memory.get("metadata", {}), **metadata}
                
                # Update timestamp
                memory["updated_at"] = datetime.now().isoformat()
                
                # Save back to file
                memories[i] = memory
                self._save_memories(memories, namespace)
                
                # Update vector database if enabled and content changed
                if self.use_vectors and self.vector_db and content is not None:
                    collection_name = f"memory_{namespace}"
                    if collection_name in self.vector_db.list_collections():
                        # Delete all chunks for this memory
                        for chunk_id in self._get_chunk_ids(memory_id, collection_name):
                            self.vector_db.delete_by_id(collection_name, chunk_id)
                        
                        # Add new chunks
                        chunks = self._chunk_text(content)
                        chunk_metadatas = []
                        for i, _ in enumerate(chunks):
                            chunk_metadata = {
                                "parent_id": memory_id,
                                "chunk_index": i,
                                "chunk_count": len(chunks),
                                **memory.get("metadata", {})
                            }
                            chunk_metadatas.append(chunk_metadata)
                        
                        self.vector_db.add_texts(
                            collection_name=collection_name,
                            texts=chunks,
                            metadatas=chunk_metadatas,
                            external_ids=[f"{memory_id}_chunk_{i}" for i in range(len(chunks))]
                        )
                
                return memory
                
        return None
    
    def delete(self, memory_id: str, namespace: str = "general") -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: The ID of the memory to delete
            namespace: The namespace where the memory is stored
            
        Returns:
            True if the memory was found and deleted, False otherwise
        """
        memories = self.get_all(namespace)
        
        # Filter out the memory to delete
        original_count = len(memories)
        memories = [m for m in memories if m.get("id") != memory_id]
        
        # If count changed, we deleted something
        if len(memories) < original_count:
            self._save_memories(memories, namespace)
            
            # Delete from vector database if enabled
            if self.use_vectors and self.vector_db:
                collection_name = f"memory_{namespace}"
                if collection_name in self.vector_db.list_collections():
                    # Delete all chunks for this memory
                    for chunk_id in self._get_chunk_ids(memory_id, collection_name):
                        self.vector_db.delete_by_id(collection_name, chunk_id)
                        
            return True
            
        return False
    
    def list_namespaces(self) -> List[str]:
        """
        List all available memory namespaces.
        
        Returns:
            List of namespace names
        """
        if not os.path.exists(self.memory_path):
            return []
            
        # Get all JSON files in the memory path
        namespaces = []
        for filename in os.listdir(self.memory_path):
            if filename.endswith(".json"):
                namespace = filename[:-5]  # Remove .json extension
                namespaces.append(namespace)
                
        return namespaces
    
    def clear_namespace(self, namespace: str) -> bool:
        """
        Clear all memories in a namespace.
        
        Args:
            namespace: The namespace to clear
            
        Returns:
            True if the namespace was cleared, False if it didn't exist
        """
        memory_file = os.path.join(self.memory_path, f"{namespace}.json")
        
        if os.path.exists(memory_file):
            # Write empty list to file
            self._save_memories([], namespace)
            
            # Clear vector database collection if enabled
            if self.use_vectors and self.vector_db:
                collection_name = f"memory_{namespace}"
                if collection_name in self.vector_db.list_collections():
                    self.vector_db.clear_collection(collection_name)
                    
            return True
            
        return False
    
    def _save_memories(self, memories: List[Dict[str, Any]], namespace: str) -> None:
        """
        Save memories to a namespace file.
        
        Args:
            memories: List of memory entries to save
            namespace: The namespace to save to
        """
        memory_file = os.path.join(self.memory_path, f"{namespace}.json")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(memory_file), exist_ok=True)
        
        # Write memories to file
        with open(memory_file, 'w') as f:
            json.dump(memories, f, indent=2)
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split long text into chunks for better semantic search.
        
        Args:
            text: The text to chunk
            
        Returns:
            List of text chunks
        """
        if not text:
            return [""]
            
        # If text is short enough, return as is
        if len(text) <= self.chunk_size:
            return [text]
            
        # Use sentence tokenization for more natural breaks
        try:
            sentences = sent_tokenize(text)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                # If adding this sentence would exceed chunk size, start a new chunk
                if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                    # But only if the current chunk is not empty
                    if current_chunk:
                        chunks.append(current_chunk)
                        # Add overlap by including the last part of previous chunk
                        words = current_chunk.split()
                        overlap = " ".join(words[-self.chunk_overlap:]) if len(words) > self.chunk_overlap else ""
                        current_chunk = overlap + " " + sentence if overlap else sentence
                    else:
                        # If sentence is longer than chunk size, just add it as its own chunk
                        chunks.append(sentence)
                        current_chunk = ""
                else:
                    # Add a space only if current_chunk is not empty
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
                        
            # Add the last chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk)
                
            return chunks
        except Exception:
            # Fallback to simple text wrapping if sentence tokenization fails
            return textwrap.wrap(
                text, 
                width=self.chunk_size, 
                replace_whitespace=False, 
                break_on_hyphens=False,
                drop_whitespace=False
            )
    
    def _vector_search(self, query: str, namespace: str, k: int = 5, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search using vector embeddings for semantic similarity.
        
        Args:
            query: The search query
            namespace: The namespace to search in
            k: Maximum number of results to return
            min_score: Minimum similarity score for results
            
        Returns:
            List of memory entries with relevance scores
        """
        collection_name = f"memory_{namespace}"
        
        # Ensure the collection exists
        if collection_name not in self.vector_db.list_collections():
            return []
            
        # Search for relevant chunks
        results = self.vector_db.search(collection_name, query, k=k*3)  # Get more chunks to group by parent
        
        # Filter by minimum score
        results = [r for r in results if r["similarity"] >= min_score]
        
        # Group chunks by parent memory and calculate combined scores
        memory_scores = defaultdict(list)
        for result in results:
            parent_id = result["metadata"].get("parent_id")
            if parent_id:
                memory_scores[parent_id].append(result["similarity"])
        
        # Get full memory entries and combine with scores
        memories = self.get_all(namespace)
        memory_dict = {m["id"]: m for m in memories}
        
        # Prepare results sorted by relevance
        ranked_results = []
        for parent_id, scores in memory_scores.items():
            if parent_id in memory_dict:
                memory = memory_dict[parent_id].copy()
                
                # Calculate aggregate score (max score among chunks)
                if scores:
                    max_score = max(scores)
                    memory["relevance_score"] = max_score
                    memory["matching_chunks"] = len(scores)
                    ranked_results.append(memory)
        
        # Sort by relevance score
        ranked_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Limit to k results
        return ranked_results[:k]
    
    def _text_search(self, query: str, namespace: str) -> List[Dict[str, Any]]:
        """
        Fallback search using simple text matching.
        
        Args:
            query: The search query
            namespace: The namespace to search in
            
        Returns:
            List of matching memory entries
        """
        memories = self.get_all(namespace)
        
        # Simple text matching search
        results = []
        query = query.lower()
        
        for memory in memories:
            content = memory.get("content", "").lower()
            
            # Check for exact match first
            if query in content:
                # Simple relevance scoring based on occurrence count and position
                count = content.count(query)
                position = content.find(query) / max(1, len(content))  # Normalized position (earlier is better)
                
                # Higher score for more occurrences and earlier position
                relevance = (count / 10.0) + (1.0 - position)
                
                # Add memory with score
                memory_with_score = memory.copy()
                memory_with_score["relevance_score"] = min(relevance, 1.0)  # Cap at 1.0
                results.append(memory_with_score)
        
        # Sort by relevance
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results
    
    def _get_chunk_ids(self, memory_id: str, collection_name: str) -> List[str]:
        """
        Get all chunk IDs associated with a memory.
        
        Args:
            memory_id: The parent memory ID
            collection_name: The vector collection name
            
        Returns:
            List of chunk IDs
        """
        chunk_ids = []
        i = 0
        while True:
            chunk_id = f"{memory_id}_chunk_{i}"
            if self.vector_db.get_by_id(collection_name, chunk_id) is None:
                break
            chunk_ids.append(chunk_id)
            i += 1
            
        return chunk_ids