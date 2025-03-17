import os
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import importlib
from src.tools.vector_db_tool import VectorDBTool

class TestVectorDBTool(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create a mock for SentenceTransformer to avoid loading the actual model
        self.model_patcher = patch('src.tools.vector_db_tool.SentenceTransformer')
        self.mock_model_class = self.model_patcher.start()
        
        # Setup the mock model
        self.mock_model = MagicMock()
        self.mock_model_class.return_value = self.mock_model
        
        # Configure the mock to return fake embeddings
        def mock_encode(texts):
            # Return a fake embedding for each text
            return np.random.rand(len(texts), 384).astype(np.float32)
        
        self.mock_model.encode.side_effect = mock_encode
        
        # Initialize the VectorDBTool with the mock
        self.vector_db = VectorDBTool(base_path=self.test_dir, backend="faiss")
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        # Stop the patcher
        self.model_patcher.stop()
        
    def test_create_collection(self):
        # Create a new collection
        result = self.vector_db.create_collection("test_collection")
        self.assertTrue(result)
        
        # Verify the collection exists
        self.assertIn("test_collection", self.vector_db.list_collections())
        
        # Try to create the same collection again
        result = self.vector_db.create_collection("test_collection")
        self.assertFalse(result)
        
    def test_add_and_search(self):
        # Create a collection
        self.vector_db.create_collection("test_collection")
        
        # Add some documents
        doc_id = self.vector_db.add_text(
            "test_collection", 
            "This is a test document about AI",
            {"source": "unit test"}
        )
        
        self.assertIsNotNone(doc_id)
        
        # Add more documents
        self.vector_db.add_text("test_collection", "Another document about machine learning")
        self.vector_db.add_text("test_collection", "This document is about data science")
        
        # Search for documents
        results = self.vector_db.search("test_collection", "AI and machine learning")
        
        # Verify we got results
        self.assertEqual(len(results), 3)  # Should get all 3 docs
        
        # Each result should have expected fields
        for result in results:
            self.assertIn("id", result)
            self.assertIn("text", result)
            self.assertIn("similarity", result)
            self.assertIn("metadata", result)
            self.assertIn("timestamp", result)
        
    def test_delete_document(self):
        # Create a collection and add a document
        self.vector_db.create_collection("test_collection")
        doc_id = self.vector_db.add_text("test_collection", "Test document")
        
        # Verify the document exists
        doc = self.vector_db.get_by_id("test_collection", doc_id)
        self.assertIsNotNone(doc)
        
        # Delete the document
        result = self.vector_db.delete_by_id("test_collection", doc_id)
        self.assertTrue(result)
        
        # Verify it's gone
        doc = self.vector_db.get_by_id("test_collection", doc_id)
        self.assertIsNone(doc)
        
    def test_update_metadata(self):
        # Create a collection and add a document
        self.vector_db.create_collection("test_collection")
        doc_id = self.vector_db.add_text(
            "test_collection", 
            "Test document",
            {"source": "original"}
        )
        
        # Update the metadata
        result = self.vector_db.update_metadata(
            "test_collection", 
            doc_id, 
            {"source": "updated", "importance": "high"}
        )
        self.assertTrue(result)
        
        # Verify the metadata was updated
        doc = self.vector_db.get_by_id("test_collection", doc_id)
        self.assertEqual(doc["metadata"]["source"], "updated")
        self.assertEqual(doc["metadata"]["importance"], "high")
        
    def test_clear_collection(self):
        # Create a collection and add documents
        self.vector_db.create_collection("test_collection")
        self.vector_db.add_text("test_collection", "Doc 1")
        self.vector_db.add_text("test_collection", "Doc 2")
        
        # Verify documents exist
        results = self.vector_db.search("test_collection", "Doc")
        self.assertEqual(len(results), 2)
        
        # Clear the collection
        result = self.vector_db.clear_collection("test_collection")
        self.assertTrue(result)
        
        # Verify it's empty
        stats = self.vector_db.get_collection_stats("test_collection")
        self.assertEqual(stats["document_count"], 0)
        
    def test_delete_collection(self):
        # Create and populate a collection
        self.vector_db.create_collection("to_delete")
        self.vector_db.add_text("to_delete", "This will be deleted")
        
        # Verify it exists
        self.assertIn("to_delete", self.vector_db.list_collections())
        
        # Delete it
        result = self.vector_db.delete_collection("to_delete")
        self.assertTrue(result)
        
        # Verify it's gone
        self.assertNotIn("to_delete", self.vector_db.list_collections())
        
    def test_add_texts_batch(self):
        # Create a collection
        self.vector_db.create_collection("batch_test")
        
        # Add multiple texts at once
        texts = ["Doc 1", "Doc 2", "Doc 3"]
        metadatas = [
            {"source": "source1"},
            {"source": "source2"},
            {"source": "source3"}
        ]
        
        doc_ids = self.vector_db.add_texts("batch_test", texts, metadatas)
        
        # Verify we got the right number of IDs back
        self.assertEqual(len(doc_ids), 3)
        
        # Verify all documents were added
        for i, doc_id in enumerate(doc_ids):
            doc = self.vector_db.get_by_id("batch_test", doc_id)
            self.assertEqual(doc["text"], texts[i])
            self.assertEqual(doc["metadata"]["source"], metadatas[i]["source"])

    def test_available_backends(self):
        # Get available backends
        backends = self.vector_db.available_backends()
        
        # Check that FAISS is available
        self.assertIn("faiss", backends)
        
    def test_current_backend(self):
        # Check current backend
        backend = self.vector_db.current_backend()
        
        # Should be FAISS as specified in setUp
        self.assertEqual(backend, "faiss")


class TestMultipleBackends(unittest.TestCase):
    """Tests for different vector database backends."""
    
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create a mock for SentenceTransformer
        self.model_patcher = patch('src.tools.vector_db_tool.SentenceTransformer')
        self.mock_model_class = self.model_patcher.start()
        
        # Setup the mock model
        self.mock_model = MagicMock()
        self.mock_model_class.return_value = self.mock_model
        
        # Configure the mock to return fake embeddings
        def mock_encode(texts):
            return np.random.rand(len(texts), 384).astype(np.float32)
        
        self.mock_model.encode.side_effect = mock_encode
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        # Stop the patcher
        self.model_patcher.stop()
    
    def test_faiss_backend(self):
        """Test FAISS backend functionality."""
        # Create VectorDBTool with FAISS backend
        vector_db = VectorDBTool(base_path=f"{self.test_dir}/faiss", backend="faiss")
        
        # Test basic operations
        vector_db.create_collection("test_collection")
        
        # Add document
        doc_id = vector_db.add_text(
            collection_name="test_collection",
            text="This is a test document for FAISS backend",
            metadata={"backend": "faiss"}
        )
        
        # Search
        results = vector_db.search(
            collection_name="test_collection",
            query="test document"
        )
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metadata"]["backend"], "faiss")
    
    def test_chroma_backend(self):
        """Test ChromaDB backend if available."""
        # Check if ChromaDB is available
        chromadb_spec = importlib.util.find_spec("chromadb")
        if chromadb_spec is None:
            self.skipTest("ChromaDB not installed")
            
        try:
            # Create VectorDBTool with ChromaDB backend
            vector_db = VectorDBTool(base_path=f"{self.test_dir}/chroma", backend="chroma")
            
            # Test basic operations
            vector_db.create_collection("test_collection")
            
            # Add document
            doc_id = vector_db.add_text(
                collection_name="test_collection",
                text="This is a test document for ChromaDB backend",
                metadata={"backend": "chroma"}
            )
            
            # Search
            results = vector_db.search(
                collection_name="test_collection",
                query="test document"
            )
            
            # Verify results
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["metadata"]["backend"], "chroma")
        except (ImportError, ValueError) as e:
            self.skipTest(f"ChromaDB backend test skipped: {e}")
            
    def test_milvus_backend(self):
        """Test Milvus backend if available."""
        # Check if PyMilvus is available
        milvus_spec = importlib.util.find_spec("pymilvus")
        if milvus_spec is None:
            self.skipTest("PyMilvus not installed")
            
        try:
            # Create VectorDBTool with Milvus backend
            # We'll use a mock server URI that won't connect for testing
            # This is to avoid requiring an actual Milvus server
            with patch('src.tools.vector_db_tool.MilvusBackend') as mock_milvus:
                # Configure the mock
                mock_instance = mock_milvus.return_value
                mock_instance.create_collection.return_value = True
                mock_instance.add_embeddings.return_value = True
                mock_instance.list_collections.return_value = ["test_collection"]
                mock_instance.search_by_embedding.return_value = ([0], [0.1])
                mock_instance.get_collection_size.return_value = 1
                
                # Create VectorDBTool with mock backend
                vector_db = VectorDBTool(
                    base_path=f"{self.test_dir}/milvus", 
                    backend="milvus"
                )
                
                # Verify basic operations work with the mock
                self.assertEqual(vector_db.backend_name, "milvus")
                self.assertTrue(vector_db.create_collection("test_collection"))
                
                # Test that the methods delegated to the backend correctly
                self.assertTrue(mock_instance.create_collection.called)
                
        except (ImportError, ValueError) as e:
            self.skipTest(f"Milvus backend test skipped: {e}")


if __name__ == '__main__':
    unittest.main()