import os
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
import json
from src.tools.llm_service import (
    LLMService, LLMProvider, LocalLLM, 
    OpenAIProvider, ClaudeProvider, initialize_llm_service
)

class TestLLMProviders(unittest.TestCase):
    def test_local_llm(self):
        """Test the LocalLLM provider"""
        model_path = "/path/to/model"
        api_url = "http://localhost:8080/v1"
        local_llm = LocalLLM(model_path, api_url)
        
        # Test capabilities
        capabilities = local_llm.capabilities
        self.assertEqual(capabilities["type"], "local")
        self.assertEqual(capabilities["privacy"], "high")
        
        # Test generation
        result = local_llm.generate("Test prompt")
        self.assertIn(model_path, result)
        self.assertIn("Test prompt", result)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_openai_provider(self):
        """Test the OpenAIProvider with environment variable"""
        openai_provider = OpenAIProvider(model="gpt-4o")
        
        # Test capabilities
        capabilities = openai_provider.capabilities
        self.assertEqual(capabilities["type"], "openai")
        self.assertEqual(capabilities["model"] if "model" in capabilities else openai_provider.model, "gpt-4o")
        
        # Test generation
        result = openai_provider.generate("Test prompt")
        self.assertIn("OpenAI", result)
        self.assertIn("gpt-4o", result)
        
    def test_openai_provider_with_key(self):
        """Test the OpenAIProvider with explicit API key"""
        openai_provider = OpenAIProvider(api_key="test_key", model="gpt-3.5-turbo")
        
        # Test capabilities
        capabilities = openai_provider.capabilities
        self.assertEqual(capabilities["type"], "openai")
        
        # Ensure model-specific capabilities are correctly set
        self.assertIn("coding", capabilities)
        self.assertIn("reasoning", capabilities)
        self.assertIn("context_length", capabilities)
        
        # Test generation
        result = openai_provider.generate("Test prompt")
        self.assertIn("OpenAI", result)
        self.assertIn("gpt-3.5-turbo", result)
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_claude_provider(self):
        """Test the ClaudeProvider with environment variable"""
        claude_provider = ClaudeProvider(model="claude-3-opus-20240229")
        
        # Test capabilities
        capabilities = claude_provider.capabilities
        self.assertEqual(capabilities["type"], "claude")
        
        # Test different Claude model variations
        opus_capabilities = claude_provider.capabilities
        self.assertEqual(opus_capabilities["reasoning"], 5)
        
        # Test with different model
        claude_provider.model = "claude-3-sonnet-20240229"
        sonnet_capabilities = claude_provider.capabilities
        self.assertEqual(sonnet_capabilities["reasoning"], 4)
        
        # Test with haiku model
        claude_provider.model = "claude-3-haiku-20240307"
        haiku_capabilities = claude_provider.capabilities
        self.assertEqual(haiku_capabilities["reasoning"], 3)
        
        # Test generation
        result = claude_provider.generate("Test prompt")
        self.assertIn("Claude", result)
    
    def test_claude_provider_missing_key(self):
        """Test ClaudeProvider raises error with missing API key"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                claude_provider = ClaudeProvider()

class TestLLMService(unittest.TestCase):
    def setUp(self):
        self.service = LLMService()
        
        # Add mock providers
        self.mock_local = MagicMock(spec=LocalLLM)
        self.mock_local.generate.return_value = "Local response"
        self.mock_local.capabilities = {
            "type": "local", "coding": 3, "reasoning": 3, 
            "creativity": 3, "knowledge": 2, "privacy": "high"
        }
        
        self.mock_openai = MagicMock(spec=OpenAIProvider)
        self.mock_openai.generate.return_value = "OpenAI response"
        self.mock_openai.capabilities = {
            "type": "openai", "coding": 5, "reasoning": 5, 
            "creativity": 4, "knowledge": 5, "privacy": "low"
        }
        
        self.mock_claude = MagicMock(spec=ClaudeProvider)
        self.mock_claude.generate.return_value = "Claude response"
        self.mock_claude.capabilities = {
            "type": "claude", "coding": 4, "reasoning": 5, 
            "creativity": 5, "knowledge": 5, "privacy": "medium"
        }
        
        self.service.add_provider("local", self.mock_local)
        self.service.add_provider("openai", self.mock_openai)
        self.service.add_provider("claude", self.mock_claude)
    
    def test_add_and_get_provider(self):
        """Test adding and retrieving providers"""
        # Test retrieving existing providers
        local_provider = self.service.get_provider("local")
        self.assertEqual(local_provider, self.mock_local)
        
        openai_provider = self.service.get_provider("openai")
        self.assertEqual(openai_provider, self.mock_openai)
        
        # Test retrieving non-existent provider
        with self.assertRaises(ValueError):
            self.service.get_provider("non_existent")
    
    def test_set_and_get_preferences(self):
        """Test setting and retrieving provider preferences"""
        # Test agent preferences
        self.service.set_agent_preference("planner", "openai", "Good for planning")
        self.service.set_agent_preference("executor", "claude", "Good for execution")
        
        # Test tool preferences
        self.service.set_tool_preference("memory", "local", "Privacy-focused")
        
        # Check preferred providers
        planner_provider = self.service.get_preferred_provider("planner", "agent")
        self.assertEqual(planner_provider, self.mock_openai)
        
        executor_provider = self.service.get_preferred_provider("executor", "agent")
        self.assertEqual(executor_provider, self.mock_claude)
        
        memory_provider = self.service.get_preferred_provider("memory", "tool")
        self.assertEqual(memory_provider, self.mock_local)
        
        # Test default behavior for non-existent preference
        default_provider = self.service.get_preferred_provider("non_existent", "agent")
        self.assertEqual(default_provider, self.mock_local)  # First provider is default
    
    def test_recommend_provider(self):
        """Test provider recommendation based on task type"""
        # Test coding tasks
        coding_provider = self.service.recommend_provider("Write a Python function", "coding")
        self.assertEqual(coding_provider, "openai")  # Has highest coding score
        
        # Test reasoning tasks
        reasoning_provider = self.service.recommend_provider("Solve this logical problem", "reasoning")
        # Both OpenAI and Claude have reasoning=5, so either could be returned
        self.assertIn(reasoning_provider, ["openai", "claude"])
        
        # Test creativity tasks
        creativity_provider = self.service.recommend_provider("Write a poem", "creativity")
        self.assertEqual(creativity_provider, "claude")  # Has highest creativity score
        
        # Test knowledge tasks
        knowledge_provider = self.service.recommend_provider("Answer this factual question", "knowledge")
        # Both OpenAI and Claude have knowledge=5, so either could be returned
        self.assertIn(knowledge_provider, ["openai", "claude"])
        
        # Test default behavior
        default_provider = self.service.recommend_provider("General task", "unknown_type")
        # Should pick the provider with highest total score
        total_scores = {
            "local": sum(v for k, v in self.mock_local.capabilities.items() if isinstance(v, (int, float))),
            "openai": sum(v for k, v in self.mock_openai.capabilities.items() if isinstance(v, (int, float))),
            "claude": sum(v for k, v in self.mock_claude.capabilities.items() if isinstance(v, (int, float)))
        }
        max_score_provider = max(total_scores.items(), key=lambda x: x[1])[0]
        self.assertEqual(default_provider, max_score_provider)
    
    def test_generate(self):
        """Test text generation with specified and default providers"""
        # Test with specified provider
        openai_result = self.service.generate("Test prompt", provider_name="openai")
        self.assertEqual(openai_result, "OpenAI response")
        self.mock_openai.generate.assert_called_once_with("Test prompt")
        
        # Test with default provider (first one added should be used)
        default_result = self.service.generate("Another prompt")
        self.assertEqual(default_result, "Local response")
        self.mock_local.generate.assert_called_once_with("Another prompt")
    
    def test_list_providers(self):
        """Test listing all providers with capabilities"""
        providers_list = self.service.list_providers()
        self.assertEqual(len(providers_list), 3)
        
        # Check that each provider is included with correct name and capabilities
        provider_names = [p["name"] for p in providers_list]
        self.assertIn("local", provider_names)
        self.assertIn("openai", provider_names)
        self.assertIn("claude", provider_names)
        
        # Check capabilities are included
        for provider in providers_list:
            self.assertIn("capabilities", provider)
            self.assertIn("type", provider["capabilities"])

@patch.dict(os.environ, {
    "ENABLE_LOCAL_LLM": "true",
    "LOCAL_LLM_PATH": "/tmp/model",
    "OPENAI_API_KEY": "fake_openai_key",
    "ANTHROPIC_API_KEY": "fake_anthropic_key"
})
class TestInitializeLLMService(unittest.TestCase):
    """Test the initialize_llm_service helper function"""
    
    @patch('src.tools.llm_service.LocalLLM')
    @patch('src.tools.llm_service.OpenAIProvider')
    @patch('src.tools.llm_service.ClaudeProvider')
    def test_initialize_all_providers(self, mock_claude_class, mock_openai_class, mock_local_class):
        """Test initializing all providers when environment variables are set"""
        # Set up mocks
        mock_local = MagicMock()
        mock_openai = MagicMock()
        mock_claude = MagicMock()
        
        mock_local_class.return_value = mock_local
        mock_openai_class.return_value = mock_openai
        mock_claude_class.return_value = mock_claude
        
        # Initialize service
        service = initialize_llm_service()
        
        # Check all providers were added
        self.assertEqual(len(service.providers), 3)
        self.assertIn("local", service.providers)
        self.assertIn("gpt4o", service.providers)
        self.assertIn("claude", service.providers)
        
        # Verify correct initialization
        mock_local_class.assert_called_once_with("/tmp/model")
        mock_openai_class.assert_called_once_with(model="gpt-4o")
        mock_claude_class.assert_called_once_with()
    
    @patch.dict(os.environ, {"ENABLE_LOCAL_LLM": "false", "OPENAI_API_KEY": ""}, clear=True)
    @patch('src.tools.llm_service.LocalLLM')
    @patch('src.tools.llm_service.OpenAIProvider')
    @patch('src.tools.llm_service.ClaudeProvider')
    def test_initialize_partial_providers(self, mock_claude_class, mock_openai_class, mock_local_class):
        """Test initializing with only some providers available"""
        # Set Anthropic key only
        os.environ["ANTHROPIC_API_KEY"] = "fake_anthropic_key"
        
        # Initialize service
        service = initialize_llm_service()
        
        # Check only Claude provider was added
        self.assertEqual(len(service.providers), 1)
        self.assertIn("claude", service.providers)
        
        # Verify Claude was initialized but not others
        mock_claude_class.assert_called_once()
        mock_local_class.assert_not_called()
        mock_openai_class.assert_not_called()

if __name__ == '__main__':
    unittest.main()