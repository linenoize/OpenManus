# OpenManus Developer Getting Started Guide

This guide will help you set up, run, and extend the OpenManus project for development purposes.

## Prerequisites

- Python 3.8+ with pip
- Node.js 14+ with npm (for frontend)
- Docker and docker-compose (optional, for containerized setup)
- Git

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/OpenManus.git
cd OpenManus
```

### Backend Setup

1. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Set up credentials (if needed):

```bash
# Create a credentials folder if it doesn't exist
mkdir -p credentials
# See credentials/README.md for details on required credentials
```

### Frontend Setup

1. Install Node.js dependencies:

```bash
npm install
```

## Running the Project

### Running the Backend

```bash
# Start the backend server
python src/server.py
```

### Running the Frontend

```bash
# Start the Next.js development server
npm run dev
```

### Using Docker (Alternative)

```bash
# Build and start all services
docker-compose up

# Rebuild services if needed
docker-compose build
```

## Project Structure

```
OpenManus/
├── src/               # Main source code
│   ├── agents/        # Multi-agent system components
│   ├── tools/         # Tool implementations
│   │   └── tests/     # Tool unit tests
├── examples/          # Example usage scripts
├── docs/              # Documentation
├── credentials/       # API keys and credentials (gitignored)
├── docker/            # Docker configuration files
└── public/            # Static assets for frontend
```

## Development Workflow

### Adding a New Tool

1. Create a new file in `src/tools/` (use existing tools as templates)
2. Implement the tool interface (similar to other tools)
3. Add unit tests in `src/tools/tests/`
4. Add an example script in `examples/`
5. Document the tool API in `docs/`

Example minimal tool structure:

```python
from typing import Dict, Any, Optional

class NewTool:
    """
    Description of the new tool.
    """
    
    def __init__(self, param1: str = "default"):
        """Initialize the tool."""
        self.param1 = param1
    
    def operation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform main operation.
        
        Args:
            input_data: Input parameters
            
        Returns:
            Operation result
        """
        # Implementation
        return {"result": "success"}
```

### Running Tests

```bash
# Run all tests
python -m unittest discover

# Run specific test file
python -m unittest src/tools/tests/test_specific_tool.py
```

### Checking Code Style

```bash
# Lint code
npm run lint  # For frontend
flake8 src    # For backend (if installed)

# Check types
mypy src      # If installed
```

## Core Concepts

### Multi-Agent System

OpenManus uses a coordinator pattern:
- TaskCoordinator: Manages overall task execution
- ExecutionAgent: Handles multi-step tasks
- ToolAgent: Uses specific tools to accomplish subtasks

### Tools

Tools are modular components that provide specific functionality:
- FileManagerTool: File operations across different storage backends
- MemoryTool: Persistent memory with vector search capabilities
- VectorDBTool: Vector database for semantic operations
- CodeExecutor: Safe code execution environment
- And more...

### LLM Service

The LLM Service provides a unified interface to multiple language model providers:
- OpenAI (GPT models)
- Anthropic (Claude models)
- Local models (optional)

## Configuration

Configuration is handled through:
1. Environment variables
2. Configuration files
3. Direct parameter passing

### Important Configuration Options

- Storage paths (where tools store data)
- LLM providers and API keys
- Performance parameters
- Backend selection for tools

See each tool's documentation for specific configuration options.

## Common Development Tasks

### Implementing a New Storage Backend

To add a new storage backend to FileManagerTool:

1. Extend the base Storage class
2. Implement required methods
3. Register the backend in FileManagerTool

Example:

```python
from src.tools.file_manager import Storage

class NewStorage(Storage):
    """New storage backend implementation."""
    
    def __init__(self, base_path: str):
        super().__init__(base_path)
    
    def read_file(self, path: str) -> str:
        # Implementation
        return "file contents"
    
    # Implement other required methods
```

### Adding a New LLM Provider

To add a new LLM provider:

1. Create a provider class in the LLM service
2. Implement the provider interface
3. Register the provider in the service

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Credential issues**: Check if API keys are correctly set up in credentials folder

3. **Storage permissions**: Ensure the application has write access to data directories

### Getting Help

- Check the documentation in the `docs/` directory
- Look at example scripts in the `examples/` directory
- Review unit tests to understand expected behavior

## Contributing

1. Create a new branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Create a pull request

Follow the code style guidelines in CLAUDE.md.

## Additional Resources

- [API Documentation](./api_documentation.md)
- [Architecture Overview](./architecture.md)
- [Configuration Guide](./configuration.md)