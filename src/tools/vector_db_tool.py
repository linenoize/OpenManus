import os
import json
import numpy as np
import faiss
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer

class VectorDBTool:
    """
    Tool for vector database storage and retrieval.
    Provides semantic search capabilities using vector embeddings.
    """
    
    def __init__(self, 
                 base_path: str = "data/vectors",
                 model_name: str = "all-MiniLM-L6-v2",
                 dimension: int = 384):
        """
        Initialize vector database tool.
        
        Args:
            base_path: Path to store vector indices and metadata
            model_name: SentenceTransformer model to use for embeddings
            dimension: Embedding dimension (depends on the model)
        """
        self.base_path = Path(base_path)
        self.model_name = model_name
        self.dimension = dimension
        self.collections = {}
        self.metadata = {}
        
        # Create base directory
        os.makedirs(self.base_path, exist_ok=True)
        
        # Load embedding model
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            print("Embeddings will not be available until a valid model is provided.")
            self.model = None
            
        # Load existing collections
        self._load_collections()
    
    def create_collection(self, collection_name: str) -> bool:
        """
        Create a new vector collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if created successfully, False if already exists
        """
        if collection_name in self.collections:
            return False
            
        # Create FAISS index
        index = faiss.IndexFlatL2(self.dimension)
        self.collections[collection_name] = index
        self.metadata[collection_name] = []
        
        # Create directory for this collection
        collection_dir = self.base_path / collection_name
        os.makedirs(collection_dir, exist_ok=True)
        
        # Save empty index
        self._save_collection(collection_name)
        
        return True
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if deleted, False if not found
        """
        if collection_name not in self.collections:
            return False
            
        # Remove from memory
        del self.collections[collection_name]
        del self.metadata[collection_name]
        
        # Delete files
        collection_dir = self.base_path / collection_name
        if collection_dir.exists():
            index_path = collection_dir / "index.faiss"
            metadata_path = collection_dir / "metadata.json"
            
            if index_path.exists():
                os.remove(index_path)
            if metadata_path.exists():
                os.remove(metadata_path)
                
            # Try to remove directory
            try:
                os.rmdir(collection_dir)
            except:
                pass  # Directory might not be empty
                
        return True
    
    def list_collections(self) -> List[str]:
        """
        List all available collections.
        
        Returns:
            List of collection names
        """
        return list(self.collections.keys())
    
    def add_text(self, 
                collection_name: str, 
                text: str, 
                metadata: Optional[Dict[str, Any]] = None,
                external_id: Optional[str] = None) -> Optional[str]:
        """
        Add text to a collection.
        
        Args:
            collection_name: Name of the collection
            text: Text to add
            metadata: Optional metadata associated with the text
            external_id: Optional external ID for the document
            
        Returns:
            ID of the added document, or None if failed
        """
        if collection_name not in self.collections:
            return None
            
        # Check if embedding model is available
        if self.model is None:
            return None
            
        # Create embedding
        embedding = self.model.encode([text])[0].astype(np.float32)
        embedding = embedding.reshape(1, -1)  # Reshape for FAISS
        
        # Add to index
        index = self.collections[collection_name]
        index.add(embedding)
        
        # Create document ID
        doc_id = external_id or f"{len(self.metadata[collection_name])}"
        
        # Add metadata
        doc_metadata = {
            "id": doc_id,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.metadata[collection_name].append(doc_metadata)
        
        # Save collection
        self._save_collection(collection_name)
        
        return doc_id
    
    def add_texts(self, 
                 collection_name: str, 
                 texts: List[str], 
                 metadatas: Optional[List[Dict[str, Any]]] = None,
                 external_ids: Optional[List[str]] = None) -> List[Optional[str]]:
        """
        Add multiple texts to a collection.
        
        Args:
            collection_name: Name of the collection
            texts: List of texts to add
            metadatas: Optional list of metadata for each text
            external_ids: Optional list of external IDs
            
        Returns:
            List of document IDs, or empty list if failed
        """
        if collection_name not in self.collections:
            return []
            
        # Check if embedding model is available
        if self.model is None:
            return []
            
        # Initialize metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # Ensure lists are the same length
        if len(metadatas) != len(texts):
            raise ValueError("texts and metadatas must have the same length")
            
        # Create embeddings
        embeddings = self.model.encode(texts).astype(np.float32)
        
        # Add to index
        index = self.collections[collection_name]
        index.add(embeddings)
        
        # Add metadata and create document IDs
        doc_ids = []
        for i, (text, metadata) in enumerate(zip(texts, metadatas)):
            # Create document ID
            doc_id = external_ids[i] if external_ids and i < len(external_ids) else f"{len(self.metadata[collection_name])}"
            
            # Add metadata
            doc_metadata = {
                "id": doc_id,
                "text": text,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata
            }
            self.metadata[collection_name].append(doc_metadata)
            doc_ids.append(doc_id)
        
        # Save collection
        self._save_collection(collection_name)
        
        return doc_ids
    
    def search(self, 
              collection_name: str, 
              query: str,
              k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            collection_name: Name of the collection
            query: Query text
            k: Number of results to return
            
        Returns:
            List of documents with similarity scores
        """
        if collection_name not in self.collections:
            return []
            
        # Check if embedding model is available
        if self.model is None:
            return []
            
        # Create embedding
        query_embedding = self.model.encode([query])[0].astype(np.float32)
        query_embedding = query_embedding.reshape(1, -1)  # Reshape for FAISS
        
        # Search in index
        index = self.collections[collection_name]
        
        # Ensure k is not larger than the number of items in the index
        if index.ntotal == 0:
            return []
            
        actual_k = min(k, index.ntotal)
        distances, indices = index.search(query_embedding, actual_k)
        
        # Format results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            # Convert distance to similarity score (1 - normalized distance)
            similarity = 1.0 - min(distance / 100.0, 1.0)  # Normalize and invert
            
            # Get metadata
            metadata = self.metadata[collection_name][idx]
            
            result = {
                "id": metadata["id"],
                "text": metadata["text"],
                "metadata": metadata["metadata"],
                "timestamp": metadata["timestamp"],
                "similarity": similarity
            }
            results.append(result)
            
        return results
    
    def get_by_id(self, collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.
        
        Args:
            collection_name: Name of the collection
            doc_id: Document ID
            
        Returns:
            Document metadata if found, None otherwise
        """
        if collection_name not in self.collections:
            return None
            
        # Search for document with matching ID
        for doc in self.metadata[collection_name]:
            if doc["id"] == doc_id:
                return doc
                
        return None
    
    def delete_by_id(self, collection_name: str, doc_id: str) -> bool:
        """
        Delete document by ID.
        
        Args:
            collection_name: Name of the collection
            doc_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        if collection_name not in self.collections:
            return False
            
        # Find document index
        doc_index = None
        for i, doc in enumerate(self.metadata[collection_name]):
            if doc["id"] == doc_id:
                doc_index = i
                break
                
        if doc_index is None:
            return False
            
        # Currently FAISS doesn't support efficient individual vector deletion
        # We need to rebuild the index without the vector
        
        # Remove from metadata
        self.metadata[collection_name].pop(doc_index)
        
        # Rebuild index if we have a model
        if self.model is not None:
            # Create a new index
            new_index = faiss.IndexFlatL2(self.dimension)
            
            # Re-add all texts
            texts = [doc["text"] for doc in self.metadata[collection_name]]
            if texts:
                embeddings = self.model.encode(texts).astype(np.float32)
                new_index.add(embeddings)
                
            # Replace old index
            self.collections[collection_name] = new_index
            
            # Save collection
            self._save_collection(collection_name)
        
        return True
    
    def clear_collection(self, collection_name: str) -> bool:
        """
        Clear all documents from a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if cleared, False if not found
        """
        if collection_name not in self.collections:
            return False
            
        # Create a new empty index
        new_index = faiss.IndexFlatL2(self.dimension)
        
        # Replace old index and metadata
        self.collections[collection_name] = new_index
        self.metadata[collection_name] = []
        
        # Save collection
        self._save_collection(collection_name)
        
        return True
    
    def update_metadata(self, collection_name: str, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a document.
        
        Args:
            collection_name: Name of the collection
            doc_id: Document ID
            metadata: New metadata (will be merged with existing)
            
        Returns:
            True if updated, False if not found
        """
        if collection_name not in self.collections:
            return False
            
        # Find document
        for doc in self.metadata[collection_name]:
            if doc["id"] == doc_id:
                # Update metadata by merging
                doc["metadata"] = {**doc["metadata"], **metadata}
                # Save collection
                self._save_collection(collection_name)
                return True
                
        return False
    
    def _save_collection(self, collection_name: str) -> None:
        """Save a collection to disk."""
        collection_dir = self.base_path / collection_name
        os.makedirs(collection_dir, exist_ok=True)
        
        # Save FAISS index
        index_path = collection_dir / "index.faiss"
        faiss.write_index(self.collections[collection_name], str(index_path))
        
        # Save metadata
        metadata_path = collection_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata[collection_name], f, indent=2)
    
    def _load_collections(self) -> None:
        """Load all collections from disk."""
        if not self.base_path.exists():
            return
            
        # Get all subdirectories (collections)
        for collection_dir in self.base_path.iterdir():
            if not collection_dir.is_dir():
                continue
                
            collection_name = collection_dir.name
            index_path = collection_dir / "index.faiss"
            metadata_path = collection_dir / "metadata.json"
            
            if index_path.exists() and metadata_path.exists():
                try:
                    # Load FAISS index
                    index = faiss.read_index(str(index_path))
                    
                    # Load metadata
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        
                    # Add to collections
                    self.collections[collection_name] = index
                    self.metadata[collection_name] = metadata
                except Exception as e:
                    print(f"Error loading collection {collection_name}: {e}")
    
    def get_collection_stats(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection statistics
        """
        if collection_name not in self.collections:
            return None
            
        index = self.collections[collection_name]
        
        return {
            "name": collection_name,
            "document_count": index.ntotal,
            "dimension": self.dimension,
            "embedding_model": self.model_name
        }