# OpenManus Documentation

Welcome to the OpenManus documentation. This guide will help you understand, use, and extend the OpenManus multi-agent system.

## Overview

OpenManus is a multi-agent system with pluggable tools and LLM service integration. It follows a coordinator pattern where a central component manages task distribution among specialized agents and tools.

## Documentation Sections

### Core Concepts

- [Architecture Overview](./architecture.md) - System components and their interactions
- [Getting Started Guide](./getting_started.md) - Setup and development workflow

### Tool References

- [API Documentation](./api_documentation.md) - Detailed API reference for all tools
- [Configuration Guide](./configuration.md) - Configuration options for all components

### Examples

The `examples/` directory contains example scripts demonstrating various features:

- `memory_usage.py` - Demonstrates the memory system with vector search
- `file_manager_usage.py` - Shows file operations across different storage backends
- `vector_db_usage.py` - Illustrates vector database and semantic search
- `llm_service_usage.py` - Demonstrates interaction with language models
- `code_executor_usage.py` - Shows executing code in a safe environment
- `monitoring_usage.py` - Demonstrates metrics collection and monitoring

## Key Components

### Multi-Agent System

- **TaskCoordinator**: Central orchestration component
- **ExecutionAgent**: Handles complex multi-step tasks
- **ToolAgent**: Manages direct tool operations

### Tools

- **FileManagerTool**: File operations with multiple storage backends
- **MemoryTool**: Persistent memory with vector-based semantic search
- **VectorDBTool**: Vector database for semantic similarity operations
- **CodeExecutor**: Safe execution environment for code
- **DataRetriever**: Data retrieval from various sources
- **WebBrowser**: Web browsing and content extraction
- **MonitoringTool**: System-wide metrics and monitoring

### Service Layer

- **LLM Service**: Abstraction over language model providers

## Quick Start

To get started quickly, follow these steps:

1. Check the [Getting Started Guide](./getting_started.md) for installation
2. Explore example scripts in the `examples/` directory
3. Refer to the [API Documentation](./api_documentation.md) for detailed usage

## Contributing

If you'd like to contribute to OpenManus, please review:

1. The development workflow in the [Getting Started Guide](./getting_started.md)
2. Code style guidelines in the project's CLAUDE.md file

## License

OpenManus is licensed under the terms found in the LICENSE file in the project root.