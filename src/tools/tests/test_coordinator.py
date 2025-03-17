import unittest
from unittest.mock import patch, MagicMock
import json
import os
from src.agents.coordinator import TaskCoordinator, PlannerAgent, ExecutionAgent, ToolAgent

class TestTaskCoordinator(unittest.TestCase):
    @patch('src.agents.coordinator.initialize_llm_service')
    def setUp(self, mock_initialize_llm):
        self.mock_llm_service = MagicMock()
        mock_initialize_llm.return_value = self.mock_llm_service
        
        # Initialize coordinator with mocked components
        self.coordinator = TaskCoordinator()
        
        # Replace actual agents with mocks
        self.mock_planner = MagicMock()
        self.mock_executor = MagicMock()
        self.mock_tool_agent = MagicMock()
        
        self.coordinator.agents['planner'] = self.mock_planner
        self.coordinator.agents['executor'] = self.mock_executor
        self.coordinator.agents['tool'] = self.mock_tool_agent
        
    def test_execute_task(self):
        """Test the task execution flow"""
        # Set up expected plan
        mock_plan = {
            "steps": [
                {"agent": "tool", "action": "use_tool", "tool_name": "memory", 
                 "tool_args": {"operation": "store", "content": "Test content"}}
            ]
        }
        self.mock_planner.plan_task.return_value = mock_plan
        
        # Set up execution result
        self.mock_executor.execute_plan.return_value = "Task executed successfully"
        
        # Execute a task
        result = self.coordinator.execute_task("Perform a test task")
        
        # Verify the flow
        self.mock_planner.plan_task.assert_called_once_with("Perform a test task")
        self.mock_executor.execute_plan.assert_called_once_with(
            mock_plan, self.coordinator.agents, self.coordinator.tools
        )
        
        # Check result format
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], "Task executed successfully")
    
    def test_set_llm_preference(self):
        """Test setting LLM preferences"""
        # Test setting agent preference
        self.coordinator.set_llm_preference("agent", "planner", "gpt4o", "Test reason")
        self.mock_llm_service.set_agent_preference.assert_called_once_with(
            "planner", "gpt4o", "Test reason"
        )
        
        # Reset mock
        self.mock_llm_service.reset_mock()
        
        # Test setting tool preference
        self.coordinator.set_llm_preference("tool", "memory", "claude", "Test reason")
        self.mock_llm_service.set_tool_preference.assert_called_once_with(
            "memory", "claude", "Test reason"
        )
        
        # Test invalid entity type
        with self.assertRaises(ValueError):
            self.coordinator.set_llm_preference("invalid", "name", "provider")
    
    def test_get_provider_recommendations(self):
        """Test getting provider recommendations"""
        # Set up mocked data
        self.mock_llm_service.list_providers.return_value = [
            {"name": "provider1", "capabilities": {"type": "local"}}
        ]
        self.mock_llm_service.agent_preferences = {
            "planner": {"provider": "provider1", "reason": "reason1"}
        }
        self.mock_llm_service.tool_preferences = {
            "memory": {"provider": "provider1", "reason": "reason2"}
        }
        
        # Get recommendations
        recommendations = self.coordinator.get_provider_recommendations()
        
        # Verify structure
        self.assertIn("providers", recommendations)
        self.assertIn("agent_preferences", recommendations)
        self.assertIn("tool_preferences", recommendations)
        
        # Verify contents
        self.assertEqual(recommendations["providers"], 
                         [{"name": "provider1", "capabilities": {"type": "local"}}])
        self.assertEqual(recommendations["agent_preferences"],
                         {"planner": {"provider": "provider1", "reason": "reason1"}})
        self.assertEqual(recommendations["tool_preferences"],
                         {"memory": {"provider": "provider1", "reason": "reason2"}})

class TestPlannerAgent(unittest.TestCase):
    def setUp(self):
        self.llm_service = MagicMock()
        self.planner = PlannerAgent(self.llm_service)
    
    def test_plan_task_with_llm(self):
        """Test task planning with LLM"""
        # Set up mock LLM response
        json_plan = '{"steps": [{"agent": "tool", "action": "use_tool", "tool_name": "memory", "tool_args": {"operation": "store", "content": "Test"}}]}'
        self.llm_service.generate.return_value = f"Some text before {json_plan} some text after"
        
        # Get preferred provider mock
        self.llm_service.get_preferred_provider.return_value = MagicMock()
        self.llm_service.get_preferred_provider.return_value.capabilities = {"type": "test_provider"}
        
        # Plan a task
        plan = self.planner.plan_task("Test task")
        
        # Verify LLM was used
        self.llm_service.generate.assert_called_once()
        
        # Verify plan structure
        self.assertIn("steps", plan)
        self.assertEqual(len(plan["steps"]), 1)
        self.assertEqual(plan["steps"][0]["tool_name"], "memory")
    
    def test_plan_task_json_parsing_error(self):
        """Test task planning with LLM but JSON parsing fails"""
        # Set up mock LLM response with invalid JSON
        self.llm_service.generate.return_value = "Invalid JSON response"
        
        # Get preferred provider mock
        self.llm_service.get_preferred_provider.return_value = MagicMock()
        self.llm_service.get_preferred_provider.return_value.capabilities = {"type": "test_provider"}
        
        # Plan a task
        plan = self.planner.plan_task("Test task")
        
        # Verify we get a fallback plan
        self.assertIn("steps", plan)
        self.assertTrue(len(plan["steps"]) > 0)
    
    def test_plan_task_without_llm(self):
        """Test task planning without LLM"""
        # Create planner without LLM service
        planner = PlannerAgent(None)
        
        # Plan a task
        plan = planner.plan_task("Test task")
        
        # Verify we get a fallback plan
        self.assertIn("steps", plan)
        self.assertTrue(len(plan["steps"]) > 0)

class TestExecutionAgent(unittest.TestCase):
    def setUp(self):
        self.llm_service = MagicMock()
        self.executor = ExecutionAgent(self.llm_service)
        
        # Create mock tools and agents
        self.mock_tool_agent = MagicMock()
        self.mock_tool_agent.use_tool.return_value = "Tool result"
        
        self.agents = {
            "tool": self.mock_tool_agent
        }
        
        self.tools = {
            "memory": MagicMock(),
            "web_browser": MagicMock()
        }
    
    def test_execute_plan(self):
        """Test executing a plan"""
        # Create a test plan
        plan = {
            "steps": [
                {
                    "agent": "tool", 
                    "action": "use_tool", 
                    "tool_name": "memory", 
                    "tool_args": {"operation": "store", "content": "Test content"}
                },
                {
                    "agent": "tool", 
                    "action": "use_tool", 
                    "tool_name": "web_browser", 
                    "tool_args": {"url": "example.com"}
                }
            ]
        }
        
        # Execute the plan
        result = self.executor.execute_plan(plan, self.agents, self.tools)
        
        # Verify tool agent was called for each step
        self.assertEqual(self.mock_tool_agent.use_tool.call_count, 2)
        
        # Verify results were combined
        self.assertTrue(isinstance(result, str))
        self.assertIn("Tool 'memory' used", result)
        self.assertIn("Tool 'web_browser' used", result)
    
    def test_execute_plan_with_summarization(self):
        """Test executing a plan with result summarization"""
        # Create a test plan with a single step
        plan = {
            "steps": [
                {
                    "agent": "tool", 
                    "action": "use_tool", 
                    "tool_name": "memory", 
                    "tool_args": {"operation": "store", "content": "Test content"}
                }
            ]
        }
        
        # Set up a long result to trigger summarization
        long_result = "A" * 1000  # Long enough to trigger summarization
        self.mock_tool_agent.use_tool.return_value = long_result
        
        # Set up mock LLM for summarization
        self.llm_service.generate.return_value = "Summarized result"
        self.llm_service.get_preferred_provider.return_value = MagicMock()
        self.llm_service.get_preferred_provider.return_value.capabilities = {"type": "test_provider"}
        
        # Execute the plan
        result = self.executor.execute_plan(plan, self.agents, self.tools)
        
        # Verify summarization was used
        self.llm_service.generate.assert_called_once()
        self.assertIn("Summarized result", result)
    
    def test_execute_unknown_step(self):
        """Test executing a plan with unknown step type"""
        # Create a test plan with an unknown step
        plan = {
            "steps": [
                {
                    "agent": "unknown", 
                    "action": "unknown_action"
                }
            ]
        }
        
        # Execute the plan
        result = self.executor.execute_plan(plan, self.agents, self.tools)
        
        # Verify we got an error message
        self.assertIn("Unknown step", result)

class TestToolAgent(unittest.TestCase):
    def setUp(self):
        self.llm_service = MagicMock()
        self.tool_agent = ToolAgent(self.llm_service)
        
        # Mock tools
        self.mock_web_browser = MagicMock()
        self.mock_web_browser.browse_web.return_value = "Web browser result"
        
        self.mock_code_executor = MagicMock()
        self.mock_code_executor.execute_code.return_value = "Code execution result"
        
        self.mock_memory = MagicMock()
        self.mock_memory.store.return_value = {"id": "mem1", "content": "Stored content"}
        self.mock_memory.get.return_value = {"id": "mem1", "content": "Retrieved content"}
        self.mock_memory.search.return_value = [{"id": "mem1", "content": "Search result"}]
        
        self.mock_vector_db = MagicMock()
        self.mock_vector_db.create_collection.return_value = True
        self.mock_vector_db.search.return_value = [{"id": "doc1", "text": "Search result"}]
        
        self.mock_file_manager = MagicMock()
        self.mock_file_manager.read_text.return_value = "File content"
        self.mock_file_manager.write_text.return_value = True
        
        self.tools = {
            "web_browser": self.mock_web_browser,
            "code_executor": self.mock_code_executor,
            "memory": self.mock_memory,
            "vector_db": self.mock_vector_db,
            "file_manager": self.mock_file_manager,
            "data_retriever": MagicMock(),
            "llm_service": self.llm_service
        }
    
    def test_use_web_browser(self):
        """Test using the web browser tool"""
        result = self.tool_agent.use_tool(
            "web_browser", 
            {"url": "https://example.com"}, 
            self.tools
        )
        
        self.mock_web_browser.browse_web.assert_called_once_with(url="https://example.com")
        self.assertEqual(result, "Web browser result")
    
    def test_use_code_executor(self):
        """Test using the code executor tool"""
        result = self.tool_agent.use_tool(
            "code_executor", 
            {"code": "print('hello')", "language": "python"}, 
            self.tools
        )
        
        self.mock_code_executor.execute_code.assert_called_once_with(
            code="print('hello')", language="python"
        )
        self.assertEqual(result, "Code execution result")
    
    def test_use_memory_tool(self):
        """Test using memory tool with different operations"""
        # Test store operation
        store_result = self.tool_agent.use_tool(
            "memory", 
            {"operation": "store", "content": "Test content", "namespace": "test"}, 
            self.tools
        )
        self.mock_memory.store.assert_called_once_with(content="Test content", namespace="test")
        self.assertIn("stored", store_result.lower())
        
        # Test get operation
        get_result = self.tool_agent.use_tool(
            "memory", 
            {"operation": "get", "memory_id": "mem1", "namespace": "test"}, 
            self.tools
        )
        self.mock_memory.get.assert_called_once_with(memory_id="mem1", namespace="test")
        self.assertEqual(get_result, {"id": "mem1", "content": "Retrieved content"})
        
        # Test search operation
        search_result = self.tool_agent.use_tool(
            "memory", 
            {"operation": "search", "query": "test", "namespace": "test"}, 
            self.tools
        )
        self.mock_memory.search.assert_called_once_with(query="test", namespace="test")
        self.assertIn("Found", search_result)
    
    def test_use_vector_db_tool(self):
        """Test using vector database tool with different operations"""
        # Test create collection
        create_result = self.tool_agent.use_tool(
            "vector_db", 
            {"operation": "create_collection", "collection_name": "test_collection"}, 
            self.tools
        )
        self.mock_vector_db.create_collection.assert_called_once_with(collection_name="test_collection")
        self.assertIn("Collection created", create_result)
        
        # Test search
        search_result = self.tool_agent.use_tool(
            "vector_db", 
            {"operation": "search", "collection_name": "test_collection", "query": "test"}, 
            self.tools
        )
        self.mock_vector_db.search.assert_called_once_with(collection_name="test_collection", query="test")
        self.assertIn("Found", search_result)
    
    def test_use_file_manager_tool(self):
        """Test using file manager tool with different operations"""
        # Test read_text operation
        read_result = self.tool_agent.use_tool(
            "file_manager", 
            {"operation": "read_text", "path": "/test/file.txt"}, 
            self.tools
        )
        self.mock_file_manager.read_text.assert_called_once_with(path="/test/file.txt")
        self.assertIn("File content", read_result)
        
        # Test write_text operation
        write_result = self.tool_agent.use_tool(
            "file_manager", 
            {"operation": "write_text", "path": "/test/file.txt", "content": "New content"}, 
            self.tools
        )
        self.mock_file_manager.write_text.assert_called_once_with(path="/test/file.txt", content="New content")
        self.assertIn("successfully", write_result.lower())
    
    def test_use_llm_service_tool(self):
        """Test using LLM service as a tool"""
        self.llm_service.generate.return_value = "Generated text"
        
        result = self.tool_agent.use_tool(
            "llm_service", 
            {"prompt": "Generate something"}, 
            self.tools
        )
        
        self.llm_service.generate.assert_called_once_with("Generate something", provider_name=None)
        self.assertEqual(result, "Generated text")
    
    def test_unknown_tool(self):
        """Test using an unknown tool"""
        result = self.tool_agent.use_tool(
            "unknown_tool", 
            {}, 
            self.tools
        )
        
        self.assertIn("not found", result)
    
    def test_unknown_operation(self):
        """Test using a tool with an unknown operation"""
        # Test memory with unknown operation
        mem_result = self.tool_agent.use_tool(
            "memory", 
            {"operation": "unknown_op"}, 
            self.tools
        )
        self.assertIn("Unknown memory operation", mem_result)
        
        # Test vector_db with unknown operation
        vdb_result = self.tool_agent.use_tool(
            "vector_db", 
            {"operation": "unknown_op"}, 
            self.tools
        )
        self.assertIn("Unknown vector_db operation", vdb_result)
        
        # Test file_manager with unknown operation
        fm_result = self.tool_agent.use_tool(
            "file_manager", 
            {"operation": "unknown_op"}, 
            self.tools
        )
        self.assertIn("Unknown file_manager operation", fm_result)
    
    def test_missing_operation(self):
        """Test using a tool without specifying an operation"""
        # Test memory with missing operation
        mem_result = self.tool_agent.use_tool(
            "memory", 
            {}, 
            self.tools
        )
        self.assertIn("requires an 'operation'", mem_result)
        
        # Test llm_service with missing prompt
        llm_result = self.tool_agent.use_tool(
            "llm_service", 
            {}, 
            self.tools
        )
        self.assertIn("requires a 'prompt'", llm_result)

if __name__ == '__main__':
    unittest.main()