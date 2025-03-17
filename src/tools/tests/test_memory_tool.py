import os
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from src.tools.memory_tool import MemoryTool

class TestMemoryTool(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        # Create another directory for vector DB
        self.vector_dir = tempfile.mkdtemp()
        
        # Initialize with vector search disabled for basic tests
        self.memory_tool = MemoryTool(
            memory_path=self.test_dir,
            use_vectors=False  # Disable vector search for basic tests
        )
        
    def tearDown(self):
        # Clean up the temporary directories
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.vector_dir)
        
    def test_store_and_retrieve(self):
        # Store a memory
        content = "This is a test memory"
        metadata = {"source": "unit test", "importance": "high"}
        memory = self.memory_tool.store(content, metadata, namespace="test")
        
        # Verify the memory has an ID
        self.assertIn("id", memory)
        memory_id = memory["id"]
        
        # Retrieve the memory by ID
        retrieved = self.memory_tool.get(memory_id, namespace="test")
        
        # Verify the content and metadata match
        self.assertEqual(retrieved["content"], content)
        self.assertEqual(retrieved["metadata"]["source"], "unit test")
        self.assertEqual(retrieved["metadata"]["importance"], "high")
        
    def test_text_search(self):
        # Store some memories
        self.memory_tool.store("apple banana orange", namespace="fruits")
        self.memory_tool.store("carrot celery lettuce", namespace="vegetables")
        self.memory_tool.store("apple pie recipe", namespace="recipes")
        
        # Search for 'apple'
        results = self.memory_tool.search("apple", namespace="fruits")
        self.assertEqual(len(results), 1)
        
        # Verify relevance scoring is included
        self.assertIn("relevance_score", results[0])
        self.assertTrue(0 <= results[0]["relevance_score"] <= 1.0)
        
        # Search across all namespaces
        all_results = []
        for namespace in ["fruits", "recipes"]:
            all_results.extend(self.memory_tool.search("apple", namespace=namespace))
        self.assertEqual(len(all_results), 2)
        
    def test_update(self):
        # Store a memory
        memory = self.memory_tool.store("Initial content", namespace="test")
        memory_id = memory["id"]
        
        # Update the memory
        updated = self.memory_tool.update(memory_id, content="Updated content", namespace="test")
        
        # Verify the update worked
        self.assertEqual(updated["content"], "Updated content")
        self.assertIn("updated_at", updated)
        
        # Retrieve and check again
        retrieved = self.memory_tool.get(memory_id, namespace="test")
        self.assertEqual(retrieved["content"], "Updated content")
        
    def test_delete(self):
        # Store a memory
        memory = self.memory_tool.store("Content to delete", namespace="test")
        memory_id = memory["id"]
        
        # Verify it exists
        self.assertIsNotNone(self.memory_tool.get(memory_id, namespace="test"))
        
        # Delete it
        result = self.memory_tool.delete(memory_id, namespace="test")
        self.assertTrue(result)
        
        # Verify it's gone
        self.assertIsNone(self.memory_tool.get(memory_id, namespace="test"))
        
    def test_namespaces(self):
        # Store memories in different namespaces
        self.memory_tool.store("Test 1", namespace="ns1")
        self.memory_tool.store("Test 2", namespace="ns2")
        self.memory_tool.store("Test 3", namespace="ns3")
        
        # List namespaces
        namespaces = self.memory_tool.list_namespaces()
        self.assertEqual(len(namespaces), 3)
        self.assertIn("ns1", namespaces)
        self.assertIn("ns2", namespaces)
        self.assertIn("ns3", namespaces)
        
        # Clear a namespace
        result = self.memory_tool.clear_namespace("ns1")
        self.assertTrue(result)
        
        # Verify the namespace is empty but still exists
        memories = self.memory_tool.get_all(namespace="ns1")
        self.assertEqual(len(memories), 0)
    
    def test_text_chunking(self):
        # Test internal chunking function
        long_text = "This is a very long text " * 50  # 1000+ characters
        chunks = self.memory_tool._chunk_text(long_text)
        
        # Verify we get multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # Verify chunk size constraints
        for chunk in chunks:
            self.assertLessEqual(len(chunk), self.memory_tool.chunk_size)
            
    @patch('src.tools.vector_db_tool.SentenceTransformer')
    @patch('src.tools.memory_tool.VectorDBTool')
    def test_vector_search(self, mock_vector_db_class, mock_model_class):
        # Create a mock vector database
        mock_vector_db = MagicMock()
        mock_vector_db_class.return_value = mock_vector_db
        
        # Configure the mock to return sample search results
        mock_vector_db.list_collections.return_value = ["memory_test"]
        mock_vector_db.search.return_value = [
            {
                "id": "memory1_chunk_0",
                "text": "This is the first chunk of memory1",
                "similarity": 0.85,
                "metadata": {"parent_id": "memory1", "chunk_index": 0}
            },
            {
                "id": "memory2_chunk_0",
                "text": "This is the first chunk of memory2",
                "similarity": 0.75,
                "metadata": {"parent_id": "memory2", "chunk_index": 0}
            }
        ]
        
        # Initialize memory tool with vector search enabled
        vector_memory = MemoryTool(
            memory_path=self.test_dir,
            use_vectors=True,
            vector_db_path=self.vector_dir
        )
        
        # Mock the get_all method to return some memories
        vector_memory.get_all = MagicMock(return_value=[
            {"id": "memory1", "content": "Memory 1 content"},
            {"id": "memory2", "content": "Memory 2 content"}
        ])
        
        # Perform vector search
        results = vector_memory.search("test query", namespace="test")
        
        # Verify the vector search was used and results are returned
        mock_vector_db.search.assert_called_once()
        self.assertEqual(len(results), 2)
        
        # Verify results have relevance scores
        self.assertIn("relevance_score", results[0])
        self.assertIn("relevance_score", results[1])
        
        # Verify results are in order of relevance (highest first)
        self.assertGreaterEqual(results[0]["relevance_score"], results[1]["relevance_score"])
    
    @patch('src.tools.vector_db_tool.SentenceTransformer')
    @patch('src.tools.memory_tool.VectorDBTool')
    def test_vector_store_and_update(self, mock_vector_db_class, mock_model_class):
        # Create a mock vector database
        mock_vector_db = MagicMock()
        mock_vector_db_class.return_value = mock_vector_db
        mock_vector_db.list_collections.return_value = []
        
        # Initialize memory tool with vector search enabled
        vector_memory = MemoryTool(
            memory_path=self.test_dir,
            use_vectors=True,
            vector_db_path=self.vector_dir
        )
        
        # Store a memory
        vector_memory.store("Test content", namespace="test")
        
        # Verify the collection was created if needed
        mock_vector_db.create_collection.assert_called_once_with("memory_test")
        
        # Verify chunks were added to the vector database
        mock_vector_db.add_texts.assert_called_once()
        
        # Update a memory
        vector_memory.get = MagicMock(return_value={
            "id": "test_id",
            "content": "Old content",
            "metadata": {}
        })
        vector_memory.update("test_id", content="Updated content", namespace="test")
        
        # Verify old chunks were deleted and new ones added
        mock_vector_db.delete_by_id.assert_called()
        self.assertEqual(mock_vector_db.add_texts.call_count, 2)  # Initial + update
        
if __name__ == '__main__':
    unittest.main()