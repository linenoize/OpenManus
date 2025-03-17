# OpenManus Configuration Guide

This document describes the configuration options available for all OpenManus components.

## Global Configuration

OpenManus uses a layered configuration approach with the following precedence (highest to lowest):

1. Direct parameter values passed to constructors
2. Environment variables
3. Configuration files
4. Default values

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENMANUS_DATA_DIR | Base directory for all data storage | "./data" |
| OPENMANUS_LOG_LEVEL | Logging level (DEBUG, INFO, WARNING, ERROR) | "INFO" |
| OPENMANUS_TEMP_DIR | Directory for temporary files | "./temp" |

### Configuration File

The main configuration file is `config.json` in the project root. Here's an example:

```json
{
  "data_dir": "./data",
  "log_level": "INFO",
  "temp_dir": "./temp",
  "tools": {
    "memory": {
      "use_vectors": true,
      "backup_enabled": true
    },
    "file_manager": {
      "default_backend": "local"
    },
    "llm": {
      "default_provider": "openai"
    }
  }
}
```

## Tool-Specific Configuration

### Memory Tool

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENMANUS_MEMORY_PATH | Path to memory storage | "data/memories" |
| OPENMANUS_VECTOR_DB_PATH | Path to vector database | "data/vectors" |
| OPENMANUS_USE_VECTORS | Enable vector search (1/0) | "0" (False) |
| OPENMANUS_MEMORY_BACKUP_ENABLED | Enable automatic backups (1/0) | "1" (True) |
| OPENMANUS_MEMORY_BACKUP_INTERVAL | Minutes between backups | "60" |

#### Configuration File (tools.memory section)

```json
{
  "tools": {
    "memory": {
      "memory_path": "data/memories",
      "use_vectors": true,
      "vector_db_path": "data/vectors",
      "model_name": "all-MiniLM-L6-v2",
      "chunk_size": 512,
      "chunk_overlap": 50,
      "backup_enabled": true,
      "backup_interval": 60
    }
  }
}
```

### Vector Database Tool

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENMANUS_VECTOR_DB_PATH | Path to vector database | "data/vectors" |
| OPENMANUS_VECTOR_MODEL | Embedding model name | "all-MiniLM-L6-v2" |
| OPENMANUS_VECTOR_DIMENSION | Embedding dimension | "384" |

#### Configuration File (tools.vector_db section)

```json
{
  "tools": {
    "vector_db": {
      "base_path": "data/vectors",
      "model_name": "all-MiniLM-L6-v2",
      "dimension": 384
    }
  }
}
```

### File Manager Tool

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENMANUS_FILE_STORAGE_PATH | Path for local file storage | "data/files" |
| OPENMANUS_GIT_STORAGE_PATH | Path for git repositories | "data/git_repos" |
| OPENMANUS_GDRIVE_TOKEN_PATH | Path to Google Drive token file | "credentials/gdrive_token.json" |
| OPENMANUS_GDRIVE_CREDENTIALS_PATH | Path to Google Drive credentials | "credentials/gdrive_credentials.json" |
| OPENMANUS_DEFAULT_FILE_BACKEND | Default storage backend (local, git, gdrive) | "local" |

#### Configuration File (tools.file_manager section)

```json
{
  "tools": {
    "file_manager": {
      "default_backend": "local",
      "backends": {
        "local": {
          "base_path": "data/files"
        },
        "git": {
          "base_path": "data/git_repos"
        },
        "gdrive": {
          "token_path": "credentials/gdrive_token.json",
          "credentials_path": "credentials/gdrive_credentials.json"
        }
      }
    }
  }
}
```

### LLM Service

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENAI_API_KEY | OpenAI API key | None |
| ANTHROPIC_API_KEY | Anthropic API key | None |
| OPENMANUS_DEFAULT_LLM | Default LLM provider (openai, anthropic, local) | "openai" |
| OPENMANUS_DEFAULT_MODEL | Default model name | "gpt-3.5-turbo" |
| OPENMANUS_MAX_TOKENS | Maximum tokens for responses | "1000" |

#### Configuration File (tools.llm section)

```json
{
  "tools": {
    "llm": {
      "default_provider": "openai",
      "default_model": "gpt-3.5-turbo",
      "max_tokens": 1000,
      "providers": {
        "openai": {
          "api_key_env": "OPENAI_API_KEY",
          "models": ["gpt-3.5-turbo", "gpt-4"]
        },
        "anthropic": {
          "api_key_env": "ANTHROPIC_API_KEY",
          "models": ["claude-2", "claude-instant-1"]
        },
        "local": {
          "host": "localhost",
          "port": 8000,
          "models": ["llama-7b"]
        }
      }
    }
  }
}
```

### Code Executor

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENMANUS_CODE_WORKSPACE | Path to code execution workspace | "data/workspace" |
| OPENMANUS_CODE_TIMEOUT | Default timeout in seconds | "5" |
| OPENMANUS_CODE_SANDBOX_TYPE | Sandbox type (docker, subprocess) | "subprocess" |

#### Configuration File (tools.code_executor section)

```json
{
  "tools": {
    "code_executor": {
      "workspace_path": "data/workspace",
      "default_timeout": 5,
      "sandbox_type": "subprocess",
      "languages": {
        "python": {
          "command": "python",
          "file_extension": ".py"
        },
        "javascript": {
          "command": "node",
          "file_extension": ".js"
        }
      }
    }
  }
}
```

### Monitoring Tool

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENMANUS_MONITORING_ENABLED | Enable monitoring (1/0) | "1" (True) |
| OPENMANUS_LOG_PATH | Path to store log files | "data/logs" |
| OPENMANUS_METRICS_PATH | Path to store metrics data | "data/metrics" |
| OPENMANUS_LOG_LEVEL | Logging level | "INFO" |
| OPENMANUS_METRICS_SAVE_INTERVAL | Seconds between metrics saves | "300" |

#### Configuration File (tools.monitoring section)

```json
{
  "tools": {
    "monitoring": {
      "enabled": true,
      "log_path": "data/logs",
      "metrics_path": "data/metrics",
      "log_level": "INFO",
      "save_interval": 300
    }
  }
}
```

## Advanced Configuration

### Custom Configuration File Location

You can specify a custom configuration file location using the environment variable:

```bash
export OPENMANUS_CONFIG_PATH="/path/to/custom/config.json"
```

### Configuration Precedence Example

Here's how configuration precedence works in practice:

1. If a parameter is directly passed to a constructor, it is used
2. Otherwise, if a matching environment variable exists, its value is used
3. Otherwise, if a value exists in the configuration file, it is used
4. Otherwise, the default value is used

Example:

```python
# Precedence 1: Direct parameter
memory = MemoryTool(memory_path="/custom/path")

# Precedence 2: Environment variable (if no direct parameter)
# export OPENMANUS_MEMORY_PATH="/env/path"
memory = MemoryTool()  # Will use "/env/path"

# Precedence 3: Config file (if no direct parameter or environment variable)
# config.json: {"tools": {"memory": {"memory_path": "/config/path"}}}
memory = MemoryTool()  # Will use "/config/path"

# Precedence 4: Default value (if nothing else specified)
memory = MemoryTool()  # Will use "data/memories"
```

## Configuration Management

### Loading Configuration

```python
from src.config import load_config

# Load config (auto-detects location)
config = load_config()

# Load from specific path
config = load_config("/path/to/config.json")

# Access values
memory_path = config.get_tool_config("memory", "memory_path")
```

### Saving Configuration

```python
from src.config import save_config

# Modify configuration
config.set_tool_config("memory", "use_vectors", True)

# Save to default location
save_config(config)

# Save to specific location
save_config(config, "/path/to/config.json")
```

## Environment Setup

### Development Environment

For development, it's recommended to use a `.env` file:

```bash
# .env file
OPENMANUS_DATA_DIR=./dev_data
OPENMANUS_LOG_LEVEL=DEBUG
OPENAI_API_KEY=your_api_key_here
```

Load environment variables with:

```python
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
```

### Production Environment

For production, set environment variables in your deployment environment.