import os
import json
import numpy as np
import importlib.util
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Type
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorDBBackend(ABC):
    """Abstract base class for vector database backends."""
    
    @abstractmethod
    def __init__(self, dimension: int, base_path: Path, **kwargs):
        """Initialize the vector database backend."""
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str) -> bool:
        """Create a new collection."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        pass
    
    @abstractmethod
    def list_collections(self) -> List[str]:
        """List all collections."""
        pass
    
    @abstractmethod
    def add_embeddings(self, collection_name: str, embeddings: np.ndarray) -> bool:
        """Add embeddings to a collection."""
        pass
    
    @abstractmethod
    def search_by_embedding(self, collection_name: str, embedding: np.ndarray, k: int = 5) -> Tuple[List[int], List[float]]:
        """Search for similar embeddings."""
        pass
    
    @abstractmethod
    def clear_collection(self, collection_name: str) -> bool:
        """Clear all embeddings from a collection."""
        pass
    
    @abstractmethod
    def get_collection_size(self, collection_name: str) -> int:
        """Get the number of embeddings in a collection."""
        pass
    
    @abstractmethod
    def save_collection(self, collection_name: str, path: Path) -> bool:
        """Save a collection to disk."""
        pass
    
    @abstractmethod
    def load_collection(self, collection_name: str, path: Path) -> bool:
        """Load a collection from disk."""
        pass

class FaissBackend(VectorDBBackend):
    """FAISS vector database backend."""
    
    def __init__(self, dimension: int, base_path: Path, **kwargs):
        """Initialize FAISS backend."""
        self.dimension = dimension
        self.base_path = base_path
        self.collections = {}
        
        # Dynamically import FAISS
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            logger.error("FAISS not found. Please install it with 'pip install faiss-cpu' or 'pip install faiss-gpu'")
            raise
    
    def create_collection(self, collection_name: str) -> bool:
        """Create a new FAISS collection."""
        if collection_name in self.collections:
            return False
        
        # Create FAISS index
        index = self.faiss.IndexFlatL2(self.dimension)
        self.collections[collection_name] = index
        return True
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a FAISS collection."""
        if collection_name not in self.collections:
            return False
        
        del self.collections[collection_name]
        return True
    
    def list_collections(self) -> List[str]:
        """List all FAISS collections."""
        return list(self.collections.keys())
    
    def add_embeddings(self, collection_name: str, embeddings: np.ndarray) -> bool:
        """Add embeddings to a FAISS collection."""
        if collection_name not in self.collections:
            return False
        
        index = self.collections[collection_name]
        index.add(embeddings)
        return True
    
    def search_by_embedding(self, collection_name: str, embedding: np.ndarray, k: int = 5) -> Tuple[List[int], List[float]]:
        """Search for similar embeddings in a FAISS collection."""
        if collection_name not in self.collections:
            return [], []
        
        index = self.collections[collection_name]
        
        # Ensure k is not larger than the number of items in the index
        if index.ntotal == 0:
            return [], []
        
        actual_k = min(k, index.ntotal)
        distances, indices = index.search(embedding, actual_k)
        
        return indices[0].tolist(), distances[0].tolist()
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear all embeddings from a FAISS collection."""
        if collection_name not in self.collections:
            return False
        
        # Create a new empty index
        new_index = self.faiss.IndexFlatL2(self.dimension)
        self.collections[collection_name] = new_index
        return True
    
    def get_collection_size(self, collection_name: str) -> int:
        """Get the number of embeddings in a FAISS collection."""
        if collection_name not in self.collections:
            return 0
        
        return self.collections[collection_name].ntotal
    
    def save_collection(self, collection_name: str, path: Path) -> bool:
        """Save a FAISS collection to disk."""
        if collection_name not in self.collections:
            return False
        
        # Save FAISS index
        path.parent.mkdir(parents=True, exist_ok=True)
        self.faiss.write_index(self.collections[collection_name], str(path))
        return True
    
    def load_collection(self, collection_name: str, path: Path) -> bool:
        """Load a FAISS collection from disk."""
        if not path.exists():
            return False
        
        try:
            # Load FAISS index
            index = self.faiss.read_index(str(path))
            self.collections[collection_name] = index
            return True
        except Exception as e:
            logger.error(f"Error loading FAISS collection {collection_name}: {e}")
            return False

class ChromaBackend(VectorDBBackend):
    """Chromadb vector database backend."""
    
    def __init__(self, dimension: int, base_path: Path, **kwargs):
        """Initialize Chroma backend."""
        self.dimension = dimension
        self.base_path = base_path
        self.client = None
        self.collections = {}
        
        # Dynamically import ChromaDB
        try:
            import chromadb
            self.chromadb = chromadb
            
            # Initialize ChromaDB client
            persist_directory = str(base_path / "chromadb")
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # Load existing collections
            for collection in self.client.list_collections():
                self.collections[collection.name] = collection
                
        except ImportError:
            logger.error("ChromaDB not found. Please install it with 'pip install chromadb'")
            raise
    
    def create_collection(self, collection_name: str) -> bool:
        """Create a new Chroma collection."""
        if collection_name in self.collections:
            return False
        
        # Create Chroma collection
        collection = self.client.create_collection(
            name=collection_name,
            metadata={"dimension": self.dimension}
        )
        self.collections[collection_name] = collection
        return True
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a Chroma collection."""
        if collection_name not in self.collections:
            return False
        
        self.client.delete_collection(collection_name)
        del self.collections[collection_name]
        return True
    
    def list_collections(self) -> List[str]:
        """List all Chroma collections."""
        return list(self.collections.keys())
    
    def add_embeddings(self, collection_name: str, embeddings: np.ndarray) -> bool:
        """Add embeddings to a Chroma collection."""
        if collection_name not in self.collections:
            return False
        
        collection = self.collections[collection_name]
        
        # ChromaDB requires IDs for each embedding
        ids = [str(i) for i in range(len(embeddings))]
        
        collection.add(
            embeddings=embeddings.tolist(),
            ids=ids
        )
        return True
    
    def search_by_embedding(self, collection_name: str, embedding: np.ndarray, k: int = 5) -> Tuple[List[int], List[float]]:
        """Search for similar embeddings in a Chroma collection."""
        if collection_name not in self.collections:
            return [], []
        
        collection = self.collections[collection_name]
        
        # Query Chroma
        results = collection.query(
            query_embeddings=embedding.tolist(),
            n_results=k
        )
        
        # Extract indices and distances
        # Note: ChromaDB returns IDs which in our case are the string indices
        if not results["ids"] or len(results["ids"][0]) == 0:
            return [], []
            
        indices = [int(idx) for idx in results["ids"][0]]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(indices)
        
        return indices, distances
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear all embeddings from a Chroma collection."""
        if collection_name not in self.collections:
            return False
        
        # Get all IDs in the collection
        collection = self.collections[collection_name]
        
        # Get all documents
        try:
            all_docs = collection.get()
            if all_docs and "ids" in all_docs and all_docs["ids"]:
                # Delete all documents
                collection.delete(all_docs["ids"])
        except Exception as e:
            logger.error(f"Error clearing ChromaDB collection: {e}")
            return False
            
        return True
    
    def get_collection_size(self, collection_name: str) -> int:
        """Get the number of embeddings in a Chroma collection."""
        if collection_name not in self.collections:
            return 0
        
        # Get collection info
        collection = self.collections[collection_name]
        try:
            all_docs = collection.get()
            return len(all_docs["ids"]) if all_docs and "ids" in all_docs else 0
        except Exception as e:
            logger.error(f"Error getting ChromaDB collection size: {e}")
            return 0
    
    def save_collection(self, collection_name: str, path: Path) -> bool:
        """Save a Chroma collection to disk."""
        # ChromaDB automatically persists changes
        return True
    
    def load_collection(self, collection_name: str, path: Path) -> bool:
        """Load a Chroma collection from disk."""
        # ChromaDB automatically loads collections
        try:
            # Get the collection if it exists
            collection = self.client.get_collection(collection_name)
            self.collections[collection_name] = collection
            return True
        except Exception as e:
            logger.error(f"Error loading ChromaDB collection {collection_name}: {e}")
            return False

class MilvusBackend(VectorDBBackend):
    """Milvus vector database backend."""
    
    def __init__(self, dimension: int, base_path: Path, **kwargs):
        """Initialize Milvus backend."""
        self.dimension = dimension
        self.base_path = base_path
        self.uri = kwargs.get("uri", "http://localhost:19530")
        self.client = None
        self.collections = {}
        
        # Dynamically import Milvus
        try:
            from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
            self.pymilvus = {
                "connections": connections,
                "utility": utility,
                "Collection": Collection,
                "CollectionSchema": CollectionSchema,
                "FieldSchema": FieldSchema,
                "DataType": DataType
            }
            
            # Connect to Milvus server
            connections.connect(
                alias="default", 
                uri=self.uri,
                timeout=kwargs.get("timeout", 10)
            )
            
            # List existing collections
            existing_collections = utility.list_collections()
            for collection_name in existing_collections:
                self.collections[collection_name] = Collection(collection_name)
                
        except ImportError:
            logger.error("PyMilvus not found. Please install it with 'pip install pymilvus'")
            raise
    
    def create_collection(self, collection_name: str) -> bool:
        """Create a new Milvus collection."""
        if collection_name in self.collections:
            return False
        
        # Define collection schema
        id_field = self.pymilvus["FieldSchema"](
            name="id", 
            dtype=self.pymilvus["DataType"].INT64, 
            is_primary=True, 
            auto_id=True
        )
        vector_field = self.pymilvus["FieldSchema"](
            name="embedding", 
            dtype=self.pymilvus["DataType"].FLOAT_VECTOR, 
            dim=self.dimension
        )
        
        schema = self.pymilvus["CollectionSchema"](
            fields=[id_field, vector_field],
            description=f"Vector collection for {collection_name}"
        )
        
        # Create collection
        collection = self.pymilvus["Collection"](
            name=collection_name,
            schema=schema
        )
        
        # Create IVF_FLAT index for fast retrieval
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index("embedding", index_params)
        collection.load()
        
        self.collections[collection_name] = collection
        return True
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a Milvus collection."""
        if collection_name not in self.collections:
            return False
        
        # Drop the collection
        self.pymilvus["utility"].drop_collection(collection_name)
        
        # Remove from local tracking
        del self.collections[collection_name]
        return True
    
    def list_collections(self) -> List[str]:
        """List all Milvus collections."""
        return list(self.collections.keys())
    
    def add_embeddings(self, collection_name: str, embeddings: np.ndarray) -> bool:
        """Add embeddings to a Milvus collection."""
        if collection_name not in self.collections:
            return False
        
        collection = self.collections[collection_name]
        
        # Insert embeddings
        entities = [
            {"embedding": embedding.tolist()} for embedding in embeddings
        ]
        
        collection.insert(entities)
        return True
    
    def search_by_embedding(self, collection_name: str, embedding: np.ndarray, k: int = 5) -> Tuple[List[int], List[float]]:
        """Search for similar embeddings in a Milvus collection."""
        if collection_name not in self.collections:
            return [], []
        
        collection = self.collections[collection_name]
        
        # Make sure the collection is loaded
        if not collection.is_loaded:
            collection.load()
        
        # Search for similar vectors
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = collection.search(
            data=[embedding.tolist()],
            anns_field="embedding",
            param=search_params,
            limit=k,
            output_fields=["id"]
        )
        
        if not results or len(results) == 0:
            return [], []
        
        # Extract IDs and distances
        ids = [hit.id for hit in results[0]]
        distances = [hit.distance for hit in results[0]]
        
        return ids, distances
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear all embeddings from a Milvus collection."""
        if collection_name not in self.collections:
            return False
        
        # Delete all entities (not very efficient, but comprehensive)
        collection = self.collections[collection_name]
        
        # In Milvus we recreate the collection to clear it effectively
        try:
            # Get schema
            schema = collection.schema
            # Drop collection
            self.pymilvus["utility"].drop_collection(collection_name)
            # Recreate with same schema
            collection = self.pymilvus["Collection"](
                name=collection_name,
                schema=schema
            )
            # Re-create index
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            collection.load()
            
            # Update local reference
            self.collections[collection_name] = collection
            return True
        except Exception as e:
            logger.error(f"Error clearing Milvus collection: {e}")
            return False
    
    def get_collection_size(self, collection_name: str) -> int:
        """Get the number of embeddings in a Milvus collection."""
        if collection_name not in self.collections:
            return 0
        
        collection = self.collections[collection_name]
        return collection.num_entities
    
    def save_collection(self, collection_name: str, path: Path) -> bool:
        """Save a Milvus collection to disk."""
        # Milvus is a server-based database, so saving is managed by the server
        return True
    
    def load_collection(self, collection_name: str, path: Path) -> bool:
        """Load a Milvus collection from disk."""
        # Milvus is a server-based database, so loading is managed by the server
        if collection_name not in self.pymilvus["utility"].list_collections():
            return False
        
        try:
            self.collections[collection_name] = self.pymilvus["Collection"](collection_name)
            return True
        except Exception as e:
            logger.error(f"Error loading Milvus collection: {e}")
            return False


class OpenAIBackend(VectorDBBackend):
    """OpenAI Vector Store backend."""
    
    def __init__(self, dimension: int, base_path: Path, **kwargs):
        """Initialize OpenAI Vector Store backend."""
        self.dimension = dimension
        self.base_path = base_path
        self.api_key = kwargs.get("api_key", os.environ.get("OPENAI_API_KEY", ""))
        self.collections = {}
        self.metadata_dir = base_path / "openai"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.api_key:
            logger.error("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            raise ValueError("OpenAI API key not found.")
        
        # Dynamically import OpenAI client
        try:
            import openai
            self.openai = openai
            self.openai.api_key = self.api_key
            
            # Initialize client with API key
            self.client = openai.OpenAI(api_key=self.api_key)
            
            # Load existing collections from metadata files
            self._load_collections()
            
        except ImportError:
            logger.error("OpenAI Python client not found. Please install it with 'pip install openai'")
            raise
    
    def _load_collections(self):
        """Load collections metadata from disk."""
        for metadata_file in self.metadata_dir.glob("*.json"):
            collection_name = metadata_file.stem
            try:
                with open(metadata_file, 'r') as f:
                    collection_data = json.load(f)
                    self.collections[collection_name] = collection_data
            except Exception as e:
                logger.error(f"Error loading collection {collection_name}: {e}")
    
    def _save_collection_metadata(self, collection_name: str):
        """Save collection metadata to disk."""
        metadata_file = self.metadata_dir / f"{collection_name}.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.collections[collection_name], f, indent=2)
    
    def create_collection(self, collection_name: str) -> bool:
        """Create a new OpenAI vector collection."""
        if collection_name in self.collections:
            return False
        
        try:
            # Create a new vector store in OpenAI
            response = self.client.beta.vector_stores.create(
                name=collection_name,
                description=f"Vector store for {collection_name}"
            )
            
            # Store collection metadata
            self.collections[collection_name] = {
                "id": response.id,
                "name": collection_name,
                "description": f"Vector store for {collection_name}",
                "created_at": datetime.now().isoformat(),
                "files": []
            }
            
            # Save to disk
            self._save_collection_metadata(collection_name)
            
            return True
        except Exception as e:
            logger.error(f"Error creating OpenAI vector store: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete an OpenAI vector collection."""
        if collection_name not in self.collections:
            return False
        
        try:
            # Delete the vector store in OpenAI
            vector_store_id = self.collections[collection_name]["id"]
            self.client.beta.vector_stores.delete(vector_store_id=vector_store_id)
            
            # Remove from local collections
            del self.collections[collection_name]
            
            # Remove metadata file
            metadata_file = self.metadata_dir / f"{collection_name}.json"
            if metadata_file.exists():
                os.remove(metadata_file)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting OpenAI vector store: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all OpenAI vector collections."""
        return list(self.collections.keys())
    
    def add_embeddings(self, collection_name: str, embeddings: np.ndarray) -> bool:
        """Add embeddings to an OpenAI vector collection."""
        if collection_name not in self.collections:
            return False
        
        try:
            vector_store_id = self.collections[collection_name]["id"]
            
            # Convert embeddings to list format required by OpenAI
            embeddings_list = embeddings.tolist()
            file_ids = []
            
            # Generate a unique batch ID
            batch_id = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Add each embedding as a file
            for i, embedding in enumerate(embeddings_list):
                file_id = f"embedding_{batch_id}_{i}"
                
                # Create file with embedding in OpenAI vector store
                self.client.beta.vector_stores.files.create(
                    vector_store_id=vector_store_id,
                    file_id=file_id,
                    embedding=embedding
                )
                
                file_ids.append(file_id)
            
            # Update collection metadata
            self.collections[collection_name]["files"].extend(file_ids)
            self._save_collection_metadata(collection_name)
            
            return True
        except Exception as e:
            logger.error(f"Error adding embeddings to OpenAI vector store: {e}")
            return False
    
    def search_by_embedding(self, collection_name: str, embedding: np.ndarray, k: int = 5) -> Tuple[List[int], List[float]]:
        """Search for similar embeddings in an OpenAI vector collection."""
        if collection_name not in self.collections:
            return [], []
        
        try:
            vector_store_id = self.collections[collection_name]["id"]
            
            # Convert embedding to list
            query_embedding = embedding.tolist()[0]  # Extract from the 1-row array
            
            # Search for similar vectors
            response = self.client.beta.vector_stores.query(
                vector_store_id=vector_store_id,
                query_vector=query_embedding,
                limit=k
            )
            
            # Extract file IDs and scores
            file_ids = []
            scores = []
            
            for match in response.matches:
                # Get index from file ID (assuming format: embedding_YYYYMMDDHHMMSS_index)
                parts = match.file_id.split('_')
                if len(parts) >= 3:
                    try:
                        index = int(parts[-1])
                        file_ids.append(index)
                        scores.append(match.score)
                    except ValueError:
                        continue
            
            return file_ids, scores
        except Exception as e:
            logger.error(f"Error searching OpenAI vector store: {e}")
            return [], []
    
    def clear_collection(self, collection_name: str) -> bool:
        """Clear all embeddings from an OpenAI vector collection."""
        if collection_name not in self.collections:
            return False
        
        try:
            vector_store_id = self.collections[collection_name]["id"]
            file_ids = self.collections[collection_name]["files"]
            
            # Delete all files in collection
            for file_id in file_ids:
                try:
                    self.client.beta.vector_stores.files.delete(
                        vector_store_id=vector_store_id,
                        file_id=file_id
                    )
                except Exception as e:
                    logger.warning(f"Error deleting file {file_id}: {e}")
            
            # Update collection metadata
            self.collections[collection_name]["files"] = []
            self._save_collection_metadata(collection_name)
            
            return True
        except Exception as e:
            logger.error(f"Error clearing OpenAI vector store: {e}")
            return False
    
    def get_collection_size(self, collection_name: str) -> int:
        """Get the number of embeddings in an OpenAI vector collection."""
        if collection_name not in self.collections:
            return 0
        
        return len(self.collections[collection_name]["files"])
    
    def save_collection(self, collection_name: str, path: Path) -> bool:
        """Save a collection to disk."""
        # OpenAI vector stores are cloud-based, so we just save metadata
        if collection_name not in self.collections:
            return False
        
        try:
            with open(path, 'w') as f:
                json.dump(self.collections[collection_name], f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving OpenAI vector store metadata: {e}")
            return False
    
    def load_collection(self, collection_name: str, path: Path) -> bool:
        """Load a collection from disk."""
        if not path.exists():
            return False
        
        try:
            with open(path, 'r') as f:
                collection_data = json.load(f)
            
            # Check if collection exists in OpenAI
            vector_store_id = collection_data.get("id")
            try:
                # Attempt to get the vector store to verify it exists
                self.client.beta.vector_stores.retrieve(vector_store_id=vector_store_id)
                self.collections[collection_name] = collection_data
                return True
            except Exception:
                logger.warning(f"OpenAI vector store {vector_store_id} not found. Creating a new one.")
                return self.create_collection(collection_name)
        except Exception as e:
            logger.error(f"Error loading OpenAI vector store metadata: {e}")
            return False


class VectorDBTool:
    """
    Tool for vector database storage and retrieval.
    Provides semantic search capabilities using vector embeddings.
    """
    
    # Registry of available backends
    BACKENDS = {
        "faiss": FaissBackend,
        "chroma": ChromaBackend,
        "milvus": MilvusBackend,
        "openai": OpenAIBackend
    }
    
    def __init__(self, 
                 base_path: str = None,
                 model_name: str = "all-MiniLM-L6-v2",
                 dimension: int = 384,
                 backend: str = None,
                 **kwargs):
        """
        Initialize vector database tool.
        
        Args:
            base_path: Path to store vector indices and metadata. If None, uses OPENMANUS_VECTOR_DB_PATH env var or default
            model_name: SentenceTransformer model to use for embeddings
            dimension: Embedding dimension (depends on the model)
            backend: Vector database backend to use ('faiss', 'chroma', 'milvus', 'openai')
                     If None, uses VECTOR_DB_BACKEND environment variable or 'faiss' as default
            **kwargs: Additional backend-specific parameters
        """
        # Check if base_path is specified in environment variable
        if base_path is None:
            base_path = os.environ.get("OPENMANUS_VECTOR_DB_PATH", "data/vectors")
        
        self.base_path = Path(base_path)
        self.model_name = model_name
        
        # Determine backend from parameters, environment variables, or default
        if backend is None:
            # Check environment variable
            backend = os.environ.get("VECTOR_DB_BACKEND", "faiss")
            
        # Validate the backend
        if backend not in self.BACKENDS:
            logger.warning(f"Unsupported vector database backend: {backend}. Falling back to 'faiss'.")
            backend = "faiss"
            
        # Prepare backend-specific configurations from environment variables
        backend_kwargs = kwargs.copy()
        
        # For Milvus, check for MILVUS_URI environment variable
        if backend == "milvus" and "uri" not in backend_kwargs:
            milvus_uri = os.environ.get("MILVUS_URI")
            if milvus_uri:
                backend_kwargs["uri"] = milvus_uri
        self.dimension = dimension
        self.backend_name = backend
        self.metadata = {}
        
        # Create base directory
        os.makedirs(self.base_path, exist_ok=True)
        
        # Load embedding model
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            logger.warning("Embeddings will not be available until a valid model is provided.")
            self.model = None
            
        # Initialize backend
        if backend not in self.BACKENDS:
            raise ValueError(f"Unknown backend: {backend}. Available backends: {list(self.BACKENDS.keys())}")
        
        backend_class = self.BACKENDS[backend]
        self.backend = backend_class(dimension=dimension, base_path=self.base_path, **backend_kwargs)
        
        # Load metadata
        self._load_metadata()
            
    def available_backends(self) -> List[str]:
        """
        Get list of available vector database backends.
        
        Returns:
            List of backend names
        """
        return list(self.BACKENDS.keys())
    
    def current_backend(self) -> str:
        """
        Get the name of the current backend.
        
        Returns:
            Backend name
        """
        return self.backend_name
    
    def create_collection(self, collection_name: str) -> bool:
        """
        Create a new vector collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if created successfully, False if already exists
        """
        # Check if collection exists in metadata
        if collection_name in self.metadata:
            return False
            
        # Create collection in backend
        if not self.backend.create_collection(collection_name):
            return False
            
        # Initialize metadata
        self.metadata[collection_name] = []
        
        # Save metadata
        self._save_metadata(collection_name)
        
        return True
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if deleted, False if not found
        """
        # Check if collection exists
        if collection_name not in self.metadata:
            return False
            
        # Delete collection in backend
        if not self.backend.delete_collection(collection_name):
            return False
            
        # Remove from metadata
        del self.metadata[collection_name]
        
        # Delete metadata file
        metadata_path = self.base_path / collection_name / "metadata.json"
        if metadata_path.exists():
            os.remove(metadata_path)
            
        # Try to remove directory
        collection_dir = self.base_path / collection_name
        if collection_dir.exists():
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
        return list(self.metadata.keys())
    
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
        # Check if collection exists
        if collection_name not in self.metadata:
            return None
            
        # Check if embedding model is available
        if self.model is None:
            return None
            
        # Create embedding
        embedding = self.model.encode([text])[0].astype(np.float32)
        embedding = embedding.reshape(1, -1)  # Reshape for backend
        
        # Add to backend
        if not self.backend.add_embeddings(collection_name, embedding):
            return None
        
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
        
        # Save metadata
        self._save_metadata(collection_name)
        
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
        # Check if collection exists
        if collection_name not in self.metadata:
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
        
        # Add to backend
        if not self.backend.add_embeddings(collection_name, embeddings):
            return []
        
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
        
        # Save metadata
        self._save_metadata(collection_name)
        
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
        # Check if collection exists
        if collection_name not in self.metadata:
            return []
            
        # Check if embedding model is available
        if self.model is None:
            return []
            
        # Create embedding
        query_embedding = self.model.encode([query])[0].astype(np.float32)
        query_embedding = query_embedding.reshape(1, -1)  # Reshape for backend
        
        # Search in backend
        indices, distances = self.backend.search_by_embedding(collection_name, query_embedding, k)
        
        # Format results
        results = []
        for idx, distance in zip(indices, distances):
            # Convert distance to similarity score (1 - normalized distance)
            similarity = 1.0 - min(distance / 100.0, 1.0)  # Normalize and invert
            
            # Get metadata (if within range)
            if idx < len(self.metadata[collection_name]):
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
        # Check if collection exists
        if collection_name not in self.metadata:
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
        # Check if collection exists
        if collection_name not in self.metadata:
            return False
            
        # Find document index
        doc_index = None
        for i, doc in enumerate(self.metadata[collection_name]):
            if doc["id"] == doc_id:
                doc_index = i
                break
                
        if doc_index is None:
            return False
        
        # Remove from metadata
        self.metadata[collection_name].pop(doc_index)
        
        # Rebuild index if we have a model
        # Note: Most vector DBs don't support efficient individual vector deletion
        if self.model is not None:
            # Clear collection
            self.backend.clear_collection(collection_name)
            
            # Re-add all texts
            texts = [doc["text"] for doc in self.metadata[collection_name]]
            if texts:
                embeddings = self.model.encode(texts).astype(np.float32)
                self.backend.add_embeddings(collection_name, embeddings)
            
            # Save metadata
            self._save_metadata(collection_name)
        
        return True
    
    def clear_collection(self, collection_name: str) -> bool:
        """
        Clear all documents from a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if cleared, False if not found
        """
        # Check if collection exists
        if collection_name not in self.metadata:
            return False
            
        # Clear backend
        if not self.backend.clear_collection(collection_name):
            return False
        
        # Clear metadata
        self.metadata[collection_name] = []
        
        # Save metadata
        self._save_metadata(collection_name)
        
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
        # Check if collection exists
        if collection_name not in self.metadata:
            return False
            
        # Find document
        for doc in self.metadata[collection_name]:
            if doc["id"] == doc_id:
                # Update metadata by merging
                doc["metadata"] = {**doc["metadata"], **metadata}
                # Save metadata
                self._save_metadata(collection_name)
                return True
                
        return False
    
    def _save_metadata(self, collection_name: str) -> None:
        """Save metadata for a collection to disk."""
        collection_dir = self.base_path / collection_name
        os.makedirs(collection_dir, exist_ok=True)
        
        # Save metadata
        metadata_path = collection_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata[collection_name], f, indent=2)
            
    def _load_metadata(self) -> None:
        """Load metadata for all collections."""
        if not self.base_path.exists():
            return
            
        # Get all subdirectories (collections)
        for collection_dir in self.base_path.iterdir():
            if not collection_dir.is_dir():
                continue
                
            collection_name = collection_dir.name
            metadata_path = collection_dir / "metadata.json"
            
            if metadata_path.exists():
                try:
                    # Load metadata
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        
                    # Add to metadata
                    self.metadata[collection_name] = metadata
                    
                    # Ensure collection exists in backend
                    if collection_name not in self.backend.list_collections():
                        self.backend.create_collection(collection_name)
                        
                        # If we have a model, rebuild the index
                        if self.model is not None:
                            texts = [doc["text"] for doc in metadata]
                            if texts:
                                embeddings = self.model.encode(texts).astype(np.float32)
                                self.backend.add_embeddings(collection_name, embeddings)
                    
                except Exception as e:
                    logger.error(f"Error loading metadata for collection {collection_name}: {e}")
    
    def get_collection_stats(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection statistics
        """
        # Check if collection exists
        if collection_name not in self.metadata:
            return None
            
        return {
            "name": collection_name,
            "document_count": self.backend.get_collection_size(collection_name),
            "dimension": self.dimension,
            "embedding_model": self.model_name,
            "backend": self.backend_name
        }