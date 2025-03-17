#!/usr/bin/env python3
"""
Example script demonstrating the use of the LLM service in OpenManus.
This script shows how to use different LLM providers and the service's
capabilities for provider selection and management.
"""

import sys
import os
import json
from datetime import datetime
from pprint import pprint

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.tools.llm_service import (
        LLMService, LocalLLM, OpenAIProvider, ClaudeProvider
    )
except ImportError as e:
    print(f"Error importing LLM service: {e}")
    print("Please install the required dependencies.")
    sys.exit(1)

def print_section(title):
    """Helper to print formatted section titles"""
    print(f"\n{title}")
    print("=" * len(title))

def main():
    print("OpenManus LLM Service Demo")
    print("=" * 60)
    
    # Create LLM service
    llm_service = LLMService()
    print("LLM Service initialized")
    
    # Attempt to initialize providers with dummy API keys for demo
    # In production, these should be proper API keys from environment or secure storage
    print_section("1. Setting up LLM providers")
    
    # Try to initialize providers with environment variables if available
    try:
        if os.environ.get("OPENAI_API_KEY"):
            print("Using OpenAI API key from environment")
            openai_key = os.environ.get("OPENAI_API_KEY")
        else:
            print("No OpenAI API key found in environment, using placeholder for demo")
            openai_key = "demo_key"  # This won't work for actual API calls
            
        if os.environ.get("ANTHROPIC_API_KEY"):
            print("Using Anthropic API key from environment")
            claude_key = os.environ.get("ANTHROPIC_API_KEY")
        else:
            print("No Anthropic API key found in environment, using placeholder for demo")
            claude_key = "demo_key"  # This won't work for actual API calls
            
        # Add providers to the service
        llm_service.add_provider("local", LocalLLM(model_path="/path/to/local/model"))
        print("✓ Added local LLM provider")
        
        llm_service.add_provider("gpt4o", OpenAIProvider(api_key=openai_key, model="gpt-4o"))
        print("✓ Added OpenAI GPT-4o provider")
        
        llm_service.add_provider("gpt35", OpenAIProvider(api_key=openai_key, model="gpt-3.5-turbo"))
        print("✓ Added OpenAI GPT-3.5 provider")
        
        llm_service.add_provider("claude", ClaudeProvider(api_key=claude_key, model="claude-3-opus-20240229"))
        print("✓ Added Claude provider")
        
    except Exception as e:
        print(f"Error initializing LLM providers: {e}")
        print("Continuing with available providers...")
    
    # Show available providers and their capabilities
    print_section("2. Available LLM providers and capabilities")
    providers = llm_service.list_providers()
    
    for provider in providers:
        print(f"\nProvider: {provider['name']}")
        print(f"  Type: {provider['capabilities']['type']}")
        
        # Print capabilities as a formatted table
        print("  Capabilities:")
        for key, value in provider['capabilities'].items():
            if key not in ["type"]:  # Skip type as it's already shown
                print(f"    {key.capitalize()}: {value}")
    
    # Set agent preferences
    print_section("3. Setting agent preferences")
    
    # Set preferences based on agent needs
    llm_service.set_agent_preference(
        "planner", 
        "gpt4o", 
        "GPT-4o's strong reasoning and planning abilities are ideal for complex planning tasks"
    )
    print("✓ Set GPT-4o as preferred provider for planning agent")
    
    llm_service.set_agent_preference(
        "executor", 
        "claude", 
        "Claude's alignment and reliability make it well-suited for executing tasks"
    )
    print("✓ Set Claude as preferred provider for execution agent")
    
    llm_service.set_agent_preference(
        "researcher", 
        "gpt4o", 
        "GPT-4o's knowledge and research capabilities are ideal for research tasks"
    )
    print("✓ Set GPT-4o as preferred provider for research agent")
    
    # Set tool preferences
    print_section("4. Setting tool preferences")
    
    llm_service.set_tool_preference(
        "code_analyzer", 
        "gpt4o", 
        "GPT-4o's coding capabilities make it ideal for code analysis"
    )
    print("✓ Set GPT-4o as preferred provider for code analyzer tool")
    
    llm_service.set_tool_preference(
        "data_summarizer", 
        "claude", 
        "Claude's summarization abilities are well-suited for data summarization"
    )
    print("✓ Set Claude as preferred provider for data summarizer tool")
    
    llm_service.set_tool_preference(
        "simple_helpers", 
        "gpt35", 
        "GPT-3.5 is cost-effective for simple helper tools"
    )
    print("✓ Set GPT-3.5 as preferred provider for simple helper tools")
    
    llm_service.set_tool_preference(
        "memory", 
        "local", 
        "Local LLM provides privacy and efficiency for memory operations"
    )
    print("✓ Set Local LLM as preferred provider for memory tool")
    
    # Show the preferences
    print_section("5. Agent and tool preferences")
    agent_prefs = llm_service.agent_preferences
    tool_prefs = llm_service.tool_preferences
    
    print("\nAgent preferences:")
    for agent, pref in agent_prefs.items():
        print(f"  {agent}: {pref['provider']} - {pref['reason']}")
    
    print("\nTool preferences:")
    for tool, pref in tool_prefs.items():
        print(f"  {tool}: {pref['provider']} - {pref['reason']}")
    
    # Demonstrate provider recommendations based on task type
    print_section("6. Provider recommendations based on task type")
    
    task_types = [
        ("Write a complex Python function to optimize an algorithm", "coding"),
        ("Plan the architecture for a new microservice", "reasoning"),
        ("Generate creative product name ideas", "creativity"),
        ("Answer questions about historical events", "knowledge"),
        ("General task with no specific category", "general")
    ]
    
    for task, task_type in task_types:
        recommended = llm_service.recommend_provider(task, task_type)
        print(f"\nTask: {task}")
        print(f"Type: {task_type}")
        print(f"Recommended provider: {recommended}")
    
    # Demonstrate text generation (using placeholder implementations)
    print_section("7. Text generation examples (placeholders)")
    
    prompts = [
        "Explain quantum computing in simple terms",
        "Write a function to sort a list in Python",
        "Generate a creative name for a futuristic urban transportation system"
    ]
    
    for i, prompt in enumerate(prompts):
        # Get different providers for different prompts
        provider_name = list(llm_service.providers.keys())[i % len(llm_service.providers)]
        
        print(f"\nPrompt: {prompt}")
        print(f"Using provider: {provider_name}")
        
        try:
            response = llm_service.generate(prompt, provider_name=provider_name)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error generating response: {e}")
    
    # Show how to use preferred providers
    print_section("8. Using agent-preferred providers")
    
    agent_tasks = {
        "planner": "Create a task plan for building a recommendation system",
        "executor": "Execute the following code analysis task: check for security vulnerabilities",
        "researcher": "Find information about recent advances in quantum computing"
    }
    
    for agent, task in agent_tasks.items():
        print(f"\nAgent: {agent}")
        print(f"Task: {task}")
        
        try:
            # Get the preferred provider for this agent
            provider = llm_service.get_preferred_provider(agent, "agent")
            print(f"Using preferred provider: {provider.capabilities['type']}")
            
            # Generate response
            response = llm_service.generate(
                f"As a {agent}, {task}",
                provider_name=llm_service.agent_preferences[agent]['provider']
            )
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error using preferred provider: {e}")
    
    print("\nLLM Service demo complete!")
    print("=" * 60)
    print("Note: This demo uses placeholder implementations. In a real environment,")
    print("the LLM providers would make actual API calls to generate responses.")

if __name__ == "__main__":
    main()