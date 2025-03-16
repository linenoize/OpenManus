import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class MemoryTool:
    """
    Tool for storing and retrieving information across sessions.
    Provides persistent memory capabilities to the agent system.
    """
    
    def __init__(self, memory_path: str = "data/memory"):
        self.memory_path = memory_path
        # Ensure memory directory exists
        os.makedirs(self.memory_path, exist_ok=True)
    
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
    
    def search(self, query: str, namespace: str = "general") -> List[Dict[str, Any]]:
        """
        Search through stored memories for relevant information.
        
        Args:
            query: The search query
            namespace: The memory namespace to search in
            
        Returns:
            List of matching memory entries
        """
        memories = self.get_all(namespace)
        
        # Simple text matching search
        # In a real implementation, this would use vector embeddings or other semantic search
        results = []
        query = query.lower()
        
        for memory in memories:
            content = memory.get("content", "").lower()
            if query in content:
                results.append(memory)
                
        return results
    
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