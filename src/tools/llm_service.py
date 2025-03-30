import os
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union

# Set up logging
logger = logging.getLogger(__name__)

class PromptRejectedError(Exception):
    """Exception raised when a prompt is rejected by the LLM provider"""
    pass

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
        
    def is_allowed(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the prompt is allowed by this provider.
        
        Args:
            prompt: The prompt to check
            
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        # Default implementation always allows
        return True, None

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
        # Check if prompt is allowed
        allowed, reason = self.is_allowed(prompt)
        if not allowed:
            raise PromptRejectedError(f"Prompt rejected by OpenAI: {reason}")
            
        # Placeholder for OpenAI implementation
        # In real implementation, you would use the OpenAI SDK
        return f"[OpenAI: {self.model}] Response to: {prompt}"
    
    def is_allowed(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the prompt is allowed by OpenAI's content policy.
        In a real implementation, this would use OpenAI's moderation API.
        
        Args:
            prompt: The prompt to check
            
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        # Simplified implementation - in real code, this would call the moderation API
        forbidden_terms = ["hack system", "illegal access", "steal credentials", "bypass security"]
        
        for term in forbidden_terms:
            if term in prompt.lower():
                return False, f"Content policy violation detected: '{term}'"
                
        return True, None
    
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
        # Check if prompt is allowed
        allowed, reason = self.is_allowed(prompt)
        if not allowed:
            raise PromptRejectedError(f"Prompt rejected by Claude: {reason}")
            
        # Placeholder for Anthropic implementation
        # In real implementation, you would use the Anthropic SDK
        return f"[Claude: {self.model}] Response to: {prompt}"
    
    def is_allowed(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the prompt is allowed by Claude's content policy.
        In a real implementation, this would use the Anthropic SDK's
        built-in content filtering.
        
        Args:
            prompt: The prompt to check
            
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        # Simplified implementation - in reality, Claude handles this internally
        forbidden_terms = ["weapons manufacturing", "drug synthesis", "malware development", 
                          "phishing tactics", "hacking instructions"]
        
        for term in forbidden_terms:
            if term in prompt.lower():
                return False, f"Content policy violation detected: '{term}'"
                
        return True, None
    
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
        self.rejected_prompts_memory = {}  # Dictionary to store rejected prompts and their fallback routes
        self.enable_local_fallback = os.environ.get("ENABLE_LOCAL_LLM_FALLBACK", "false").lower() == "true"
        
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
        
        # Check if we have a memory entry for this prompt
        prompt_hash = hash(task_description.strip().lower())
        if prompt_hash in self.rejected_prompts_memory:
            fallback_info = self.rejected_prompts_memory[prompt_hash]
            logger.info(f"Using remembered fallback provider '{fallback_info['fallback_provider']}' for previously rejected prompt")
            return fallback_info['fallback_provider']
            
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
    
    def _find_local_fallback_provider(self) -> Optional[str]:
        """Find a local LLM provider for fallback"""
        for name, provider in self.providers.items():
            if provider.capabilities.get("type") == "local":
                return name
        return None
    
    def _remember_rejected_prompt(self, prompt: str, original_provider: str, fallback_provider: str, reason: str) -> None:
        """Store information about a rejected prompt for future reference"""
        prompt_hash = hash(prompt.strip().lower())
        self.rejected_prompts_memory[prompt_hash] = {
            "original_provider": original_provider,
            "fallback_provider": fallback_provider,
            "reason": reason,
            "timestamp": time.time()
        }
        logger.info(f"Remembered rejected prompt: {prompt[:50]}... will use {fallback_provider} in future")
    
    def generate(self, prompt: str, provider_name: str = None, **kwargs) -> str:
        """
        Generate text from a prompt using specified or default provider,
        with fallback to local LLM if enabled and the request is rejected.
        
        Args:
            prompt: The text prompt to send to the LLM
            provider_name: Optional name of specific provider to use
            **kwargs: Additional arguments to pass to the provider
            
        Returns:
            Generated text response
            
        Raises:
            ValueError: If no providers are available or provider is not found
            Exception: If generation fails and fallback is not available or also fails
        """
        # Check if we already know this prompt was rejected before
        prompt_hash = hash(prompt.strip().lower())
        if prompt_hash in self.rejected_prompts_memory:
            fallback_info = self.rejected_prompts_memory[prompt_hash]
            provider_name = fallback_info['fallback_provider']
            logger.info(f"Using remembered fallback route for previously rejected prompt: {fallback_info['reason']}")
        
        # Determine provider to use
        if provider_name:
            try:
                provider = self.get_provider(provider_name)
            except ValueError as e:
                logger.warning(f"Requested provider '{provider_name}' not found: {e}")
                if not self.providers:
                    raise ValueError("No providers available")
                provider = next(iter(self.providers.values()))
                provider_name = next(iter(self.providers.keys()))
        else:
            # Use first provider as default
            if not self.providers:
                raise ValueError("No providers available")
            provider = next(iter(self.providers.values()))
            provider_name = next(iter(self.providers.keys()))
        
        try:
            # Attempt to generate with selected provider
            return provider.generate(prompt, **kwargs)
        except PromptRejectedError as e:
            logger.warning(f"Prompt rejected by {provider_name}: {e}")
            
            # Check if local fallback is enabled
            if self.enable_local_fallback:
                local_provider_name = self._find_local_fallback_provider()
                
                if local_provider_name:
                    logger.info(f"Attempting fallback to local LLM provider '{local_provider_name}'")
                    
                    try:
                        # Try with local LLM
                        local_provider = self.get_provider(local_provider_name)
                        result = local_provider.generate(prompt, **kwargs)
                        
                        # Remember this for future requests
                        self._remember_rejected_prompt(
                            prompt, 
                            provider_name, 
                            local_provider_name, 
                            str(e)
                        )
                        
                        return result
                    except Exception as fallback_error:
                        logger.error(f"Fallback to local LLM also failed: {fallback_error}")
                        raise Exception(f"Primary provider ({provider_name}) rejected the request and "
                                       f"fallback to local LLM also failed: {fallback_error}")
                else:
                    logger.error("No local LLM provider available for fallback")
                    raise Exception(f"Request rejected by {provider_name} and no local fallback available: {e}")
            else:
                # Fallback not enabled, re-raise the original error
                raise
        except Exception as e:
            logger.error(f"Error generating text with provider {provider_name}: {e}")
            raise
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """List all available providers with their capabilities"""
        return [{"name": name, "capabilities": provider.capabilities} 
                for name, provider in self.providers.items()]
                
    def get_rejected_prompts_stats(self) -> Dict[str, Any]:
        """Get statistics about rejected prompts and fallbacks"""
        total_rejected = len(self.rejected_prompts_memory)
        fallback_providers = {}
        
        for info in self.rejected_prompts_memory.values():
            fallback = info['fallback_provider']
            if fallback in fallback_providers:
                fallback_providers[fallback] += 1
            else:
                fallback_providers[fallback] = 1
        
        return {
            "total_rejected_prompts": total_rejected,
            "fallback_providers": fallback_providers,
            "enable_local_fallback": self.enable_local_fallback
        }

# Example initialization function
def initialize_llm_service():
    """Initialize and return LLM service with available providers"""
    service = LLMService()
    
    # Log fallback configuration
    fallback_enabled = os.environ.get("ENABLE_LOCAL_LLM_FALLBACK", "false").lower() == "true"
    logger.info(f"Local LLM fallback for rejected prompts is {'ENABLED' if fallback_enabled else 'DISABLED'}")
    
    # Initialize providers based on environment variables
    try:
        if os.environ.get("ENABLE_LOCAL_LLM", "false").lower() == "true":
            model_path = os.environ.get("LOCAL_LLM_PATH", "models/mistral-7b")
            service.add_provider("local", LocalLLM(model_path))
            logger.info(f"Initialized local LLM with model: {model_path}")
            
            # If fallback is enabled, ensure we also log that a compatible provider was found
            if fallback_enabled:
                logger.info("Local LLM provider will be used for fallback when cloud providers reject prompts")
    except Exception as e:
        logger.warning(f"Failed to initialize local LLM: {e}")
        if fallback_enabled:
            logger.warning("Local LLM fallback is enabled but no local LLM could be initialized")
        
    try:
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key:
            service.add_provider("gpt4o", OpenAIProvider(model="gpt-4o"))
            logger.info("Initialized OpenAI GPT-4o provider")
        else:
            logger.warning("OpenAI API key not found in environment variables")
            # Add mock provider for development without API key
            service.add_provider("gpt4o_mock", MockProvider("openai", "gpt-4o"))
            logger.info("Added mock OpenAI provider for development")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI provider: {e}")
        # Add fallback
        service.add_provider("gpt4o_mock", MockProvider("openai", "gpt-4o"))
        
    try:
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            service.add_provider("claude", ClaudeProvider())
            logger.info("Initialized Anthropic Claude provider")
        else:
            logger.warning("Anthropic API key not found in environment variables")
            # Add mock provider for development without API key
            service.add_provider("claude_mock", MockProvider("anthropic", "claude-3-opus"))
            logger.info("Added mock Claude provider for development")
    except Exception as e:
        logger.warning(f"Failed to initialize Claude provider: {e}")
        # Add fallback
        service.add_provider("claude_mock", MockProvider("anthropic", "claude-3-opus"))
    
    # Add dummy provider in case no providers were initialized
    if not service.providers:
        logger.warning("No LLM providers initialized, adding fallback provider")
        service.add_provider("fallback", MockProvider("fallback", "text-model"))
    
    # If fallback is enabled but no local LLM is available, add a mock local provider
    if fallback_enabled and not any(p.capabilities.get("type") == "local" for p in service.providers.values()):
        logger.warning("Local LLM fallback is enabled but no local provider available, adding mock local provider")
        service.add_provider("local_mock", MockProvider("local", "mock-local-model"))
        
    return service

class MockProvider(LLMProvider):
    """Mock provider for development and testing"""
    
    def __init__(self, provider_type: str = "local", model_name: str = "mock-model"):
        self.provider_type = provider_type
        self.model_name = model_name
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using a mock response"""
        # Check if prompt is allowed
        allowed, reason = self.is_allowed(prompt)
        if not allowed:
            raise PromptRejectedError(f"Prompt rejected by mock {self.provider_type} provider: {reason}")
            
        logger.warning(f"Using mock {self.provider_type} provider ({self.model_name}) - API credentials not configured")
        return f"[Mock {self.provider_type}] This is a placeholder response. Configure {self.provider_type.upper()}_API_KEY to use the real service."
    
    def is_allowed(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """Mock implementation of content filtering"""
        # For local models, allow everything to enable fallback
        if self.provider_type == "local":
            return True, None
            
        # For other models, implement a basic filter
        forbidden_terms = {
            "openai": ["hack system", "illegal access", "bypass security"],
            "anthropic": ["weapons manufacturing", "drug synthesis", "malware development"],
            "fallback": ["illegal content", "harmful instructions"]
        }
        
        terms = forbidden_terms.get(self.provider_type, ["harmful content"])
        
        for term in terms:
            if term in prompt.lower():
                return False, f"Content policy violation detected: '{term}'"
                
        return True, None
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Return mock capabilities based on provider type"""
        if self.provider_type == "openai":
            return {
                "type": "openai_mock",
                "coding": 4,
                "reasoning": 4,
                "creativity": 4,
                "knowledge": 4,
                "context_length": 8000,
                "cost": "free",
                "latency": "fast",
                "privacy": "high"
            }
        elif self.provider_type == "anthropic":
            return {
                "type": "claude_mock",
                "coding": 4,
                "reasoning": 4,
                "creativity": 4,
                "knowledge": 4,
                "context_length": 8000,
                "cost": "free",
                "latency": "fast",
                "privacy": "high"
            }
        elif self.provider_type == "local":
            return {
                "type": "local",
                "coding": 3,
                "reasoning": 3,
                "creativity": 3,
                "knowledge": 2,
                "context_length": 4000,
                "cost": "free",
                "latency": "fast",
                "privacy": "high"
            }
        else:
            return {
                "type": "fallback_mock",
                "coding": 2,
                "reasoning": 2,
                "creativity": 2,
                "knowledge": 2,
                "context_length": 4000,
                "cost": "free",
                "latency": "fast",
                "privacy": "high"
            }