import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

# Set up logging
logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        """Return capabilities of this LLM provider"""
        pass

class LocalLLM(LLMProvider):
    """Provider for locally hosted LLMs"""
    
    def __init__(self, model_path: str, api_url: str = "http://localhost:8000/v1"):
        self.model_path = model_path
        self.api_url = api_url
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using a local model"""
        # Placeholder for local LLM implementation
        # In a real implementation, you would use a library like llama-cpp-python
        return f"[Local LLM: {self.model_path}] Response to: {prompt}"
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        return {
            "type": "local",
            "coding": 3,  # 1-5 rating scale
            "reasoning": 3,
            "creativity": 3,
            "knowledge": 2,
            "context_length": 8192,
            "cost": "free",
            "latency": "varies",
            "privacy": "high"
        }

class OpenAIProvider(LLMProvider):
    """Provider for OpenAI models"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.model = model
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API"""
        # Placeholder for OpenAI implementation
        # In real implementation, you would use the OpenAI SDK
        return f"[OpenAI: {self.model}] Response to: {prompt}"
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        capabilities = {
            "type": "openai",
            "latency": "medium",
            "privacy": "low",
            "cost": "high"
        }
        
        # Model-specific capabilities
        if self.model == "gpt-4o":
            capabilities.update({
                "coding": 5,
                "reasoning": 5,
                "creativity": 4,
                "knowledge": 5,
                "context_length": 128000
            })
        elif self.model == "gpt-3.5-turbo":
            capabilities.update({
                "coding": 4,
                "reasoning": 3,
                "creativity": 4,
                "knowledge": 4,
                "context_length": 16000
            })
            
        return capabilities

class ClaudeProvider(LLMProvider):
    """Provider for Anthropic Claude models"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        self.model = model
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Anthropic API"""
        # Placeholder for Anthropic implementation
        # In real implementation, you would use the Anthropic SDK
        return f"[Claude: {self.model}] Response to: {prompt}"
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        capabilities = {
            "type": "claude",
            "latency": "medium",
            "privacy": "medium",
            "cost": "high"
        }
        
        # Model-specific capabilities
        if "opus" in self.model:
            capabilities.update({
                "coding": 4,
                "reasoning": 5,
                "creativity": 5,
                "knowledge": 5,
                "context_length": 200000
            })
        elif "sonnet" in self.model:
            capabilities.update({
                "coding": 4,
                "reasoning": 4,
                "creativity": 4,
                "knowledge": 4,
                "context_length": 180000
            })
        elif "haiku" in self.model:
            capabilities.update({
                "coding": 3,
                "reasoning": 3,
                "creativity": 3,
                "knowledge": 3,
                "context_length": 150000
            })
            
        return capabilities

class LLMService:
    """Service to manage multiple LLM providers and recommend models for tasks"""
    
    def __init__(self):
        self.providers = {}
        self.agent_preferences = {}
        self.tool_preferences = {}
        
    def add_provider(self, name: str, provider: LLMProvider) -> None:
        """Add an LLM provider to the service"""
        self.providers[name] = provider
        
    def get_provider(self, name: str) -> LLMProvider:
        """Get a provider by name"""
        if name not in self.providers:
            raise ValueError(f"Provider {name} not found")
        return self.providers[name]
    
    def set_agent_preference(self, agent_name: str, provider_name: str, reason: str = "") -> None:
        """Set preferred provider for an agent"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found")
        self.agent_preferences[agent_name] = {
            "provider": provider_name,
            "reason": reason
        }
    
    def set_tool_preference(self, tool_name: str, provider_name: str, reason: str = "") -> None:
        """Set preferred provider for a tool"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found")
        self.tool_preferences[tool_name] = {
            "provider": provider_name,
            "reason": reason
        }
        
    def get_preferred_provider(self, agent_or_tool: str, type_: str = "agent") -> LLMProvider:
        """Get preferred provider for an agent or tool"""
        preferences = self.agent_preferences if type_ == "agent" else self.tool_preferences
        if agent_or_tool in preferences:
            provider_name = preferences[agent_or_tool]["provider"]
            return self.get_provider(provider_name)
        
        # Default to first provider if no preference set
        if not self.providers:
            raise ValueError("No providers available")
        return next(iter(self.providers.values()))
    
    def recommend_provider(self, task_description: str, task_type: str) -> str:
        """Recommend best provider based on task type and description"""
        if not self.providers:
            raise ValueError("No providers available")
            
        # Simple recommendation logic based on task type
        if task_type == "coding":
            # Find provider with highest coding score
            return max(self.providers.items(), 
                       key=lambda x: x[1].capabilities.get("coding", 0))[0]
        elif task_type == "creativity":
            return max(self.providers.items(), 
                       key=lambda x: x[1].capabilities.get("creativity", 0))[0]
        elif task_type == "reasoning":
            return max(self.providers.items(), 
                       key=lambda x: x[1].capabilities.get("reasoning", 0))[0]
        elif task_type == "knowledge":
            return max(self.providers.items(), 
                       key=lambda x: x[1].capabilities.get("knowledge", 0))[0]
        else:
            # Default to provider with best overall capabilities
            return max(self.providers.items(), 
                       key=lambda x: sum(v for k, v in x[1].capabilities.items() 
                                     if isinstance(v, (int, float))))[0]
    
    def generate(self, prompt: str, provider_name: str = None, **kwargs) -> str:
        """Generate text from a prompt using specified or default provider"""
        if provider_name:
            provider = self.get_provider(provider_name)
        else:
            # Use first provider as default
            if not self.providers:
                raise ValueError("No providers available")
            provider = next(iter(self.providers.values()))
            
        return provider.generate(prompt, **kwargs)
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """List all available providers with their capabilities"""
        return [{"name": name, "capabilities": provider.capabilities} 
                for name, provider in self.providers.items()]

# Example initialization function
def initialize_llm_service():
    """Initialize and return LLM service with available providers"""
    service = LLMService()
    
    # Initialize providers based on environment variables
    try:
        if os.environ.get("ENABLE_LOCAL_LLM", "false").lower() == "true":
            model_path = os.environ.get("LOCAL_LLM_PATH", "models/mistral-7b")
            service.add_provider("local", LocalLLM(model_path))
    except Exception as e:
        logger.warning(f"Failed to initialize local LLM: {e}")
        
    try:
        if os.environ.get("OPENAI_API_KEY"):
            service.add_provider("gpt4o", OpenAIProvider(model="gpt-4o"))
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
    try:
        if os.environ.get("ANTHROPIC_API_KEY"):
            service.add_provider("claude", ClaudeProvider())
    except Exception as e:
        logger.warning(f"Failed to initialize Claude provider: {e}")
        
    return service