import os
import json
import tempfile
import shutil
import unittest
from src.tools.memory_tool import MemoryTool

class TestMemoryTool(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.memory_tool = MemoryTool(memory_path=self.test_dir)
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
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
        
    def test_search(self):
        # Store some memories
        self.memory_tool.store("apple banana orange", namespace="fruits")
        self.memory_tool.store("carrot celery lettuce", namespace="vegetables")
        self.memory_tool.store("apple pie recipe", namespace="recipes")
        
        # Search for 'apple'
        results = self.memory_tool.search("apple", namespace="fruits")
        self.assertEqual(len(results), 1)
        
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
        
if __name__ == '__main__':
    unittest.main()