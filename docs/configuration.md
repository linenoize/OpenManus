# OpenManus Configuration Guide

This document describes the configuration options available for all OpenManus components.

## Configuration Approach

OpenManus uses a layered configuration approach with the following precedence (highest to lowest):

1. Direct parameter values passed to constructors
2. Environment variables (defined in `.env` file)
3. Configuration files
4. Default values

The recommended approach is to use the `.env` file for all configuration settings, as this provides a single location for most configuration needs.

> **Note:** As of the latest update, the configuration system has been unified. All tools now use the `Config` class from `src/config.py` to access configuration values, with consistent environment variable overrides.

## Environment Configuration (.env)

The primary configuration method is through the `.env` file in the project root directory. This file contains all environment variables that configure OpenManus.

Copy the `.env.example` file to create your own `.env` file:

```bash
cp .env.example .env
```

Then edit the `.env` file to customize your configuration.

### Core Settings

```bash
# Base path for all data storage
OPENMANUS_DATA_DIR=./data
# Logging level (DEBUG, INFO, WARNING, ERROR)
OPENMANUS_LOG_LEVEL=INFO
# Directory for temporary files
OPENMANUS_TEMP_DIR=./temp
```

### API and Service Configuration

```bash
# Port configuration
FRONTEND_PORT=3000
API_PORT=5000
TOOLS_PORT=5001

# API client configuration
API_HOST=localhost
API_PATH=api  # API path prefix (used in unified setup)
```

### LLM Provider Settings

```bash
# Default LLM preferences
DEFAULT_PLANNER_LLM=gpt4o
DEFAULT_EXECUTOR_LLM=claude
DEFAULT_TOOLAGENT_LLM=local
OPENMANUS_DEFAULT_LLM=openai
OPENMANUS_DEFAULT_MODEL=gpt-3.5-turbo
OPENMANUS_MAX_TOKENS=1000

# OpenAI settings
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic settings
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Local LLM settings
ENABLE_LOCAL_LLM=true
LOCAL_LLM_PATH=models/llama3
LOCAL_LLM_API_URL=http://localhost:8000/v1
```

### File Storage Configuration

```bash
# Default storage backend
OPENMANUS_DEFAULT_FILE_BACKEND=local

# Path configuration
OPENMANUS_FILE_STORAGE_PATH=data/files/local
OPENMANUS_GIT_STORAGE_PATH=data/files/git

# Git backend settings
OPENMANUS_GIT_USER_NAME=OpenManus
OPENMANUS_GIT_USER_EMAIL=openmanus@example.com

# Google Drive settings
GOOGLE_DRIVE_CLIENT_ID=your_client_id
GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret
GOOGLE_DRIVE_REDIRECT_URI=http://localhost:8080
OPENMANUS_GDRIVE_TOKEN_PATH=credentials/gdrive_token.json
OPENMANUS_GDRIVE_CREDENTIALS_PATH=credentials/gdrive_credentials.json
OPENMANUS_GDRIVE_ROOT_FOLDER=OpenManus

# OneDrive settings
OPENMANUS_ONEDRIVE_CREDENTIALS_PATH=credentials/onedrive_credentials.json
OPENMANUS_ONEDRIVE_ROOT_FOLDER=OpenManus

# Storage preferences by file type
OPENMANUS_STORAGE_TEMP=local
OPENMANUS_STORAGE_CODE=git
OPENMANUS_STORAGE_KNOWLEDGE=git
OPENMANUS_STORAGE_DOCUMENT=google_drive
OPENMANUS_STORAGE_IMAGE=google_drive
OPENMANUS_STORAGE_VIDEO=google_drive
OPENMANUS_STORAGE_AUDIO=google_drive
OPENMANUS_STORAGE_GENERAL=local
```

### Memory Tool Configuration

```bash
OPENMANUS_MEMORY_PATH=data/memories
OPENMANUS_USE_VECTORS=1  # Enable vector search (1/0)
OPENMANUS_MEMORY_BACKUP_ENABLED=1  # Enable automatic backups (1/0)
OPENMANUS_MEMORY_BACKUP_INTERVAL=60  # Minutes between backups
```

### Vector Database Configuration

```bash
OPENMANUS_VECTOR_DB_PATH=data/vectors
OPENMANUS_VECTOR_MODEL=all-MiniLM-L6-v2  # Embedding model name
OPENMANUS_VECTOR_DIMENSION=384  # Embedding dimension
VECTOR_DB_BACKEND=faiss  # Vector database backend (faiss, chroma, milvus)
```

### Code Executor Configuration

```bash
OPENMANUS_CODE_WORKSPACE=data/workspace  # Path to code execution workspace
OPENMANUS_CODE_TIMEOUT=5  # Default timeout in seconds
OPENMANUS_CODE_SANDBOX_TYPE=subprocess  # Sandbox type (docker, subprocess)
```

### Monitoring Configuration

```bash
OPENMANUS_MONITORING_ENABLED=1  # Enable monitoring (1/0)
OPENMANUS_LOG_PATH=data/logs  # Path to store log files
OPENMANUS_METRICS_PATH=data/metrics  # Path to store metrics data
OPENMANUS_METRICS_SAVE_INTERVAL=300  # Seconds between metrics saves
```

### Task Decomposition Configuration

```bash
OPENMANUS_TASK_STORAGE_PATH=data/tasks  # Path to store task data
OPENMANUS_TASK_NOTIFICATIONS=0  # Enable task status notifications (1/0)
```

### Document Processing Configuration

```bash
OPENMANUS_DOCUMENT_CACHE_DIR=data/document_cache  # Path to cache processed documents
OPENMANUS_DOCUMENT_ENABLE_OCR=0  # Enable OCR capabilities (1/0)
OPENMANUS_DOCUMENT_ENABLE_ADVANCED=0  # Enable advanced document analysis (1/0)
```

### Web Browser Tool Configuration

```bash
WEB_BROWSER_API_KEY=your_web_browser_api_key_here
```

## Configuration Files (Alternative)

While the `.env` file is the recommended configuration method, OpenManus also supports JSON configuration files for more complex setups or when environment variables are not practical.

### Main Configuration File

The main configuration file is `config.json` in the project root directory (or specified by the `OPENMANUS_CONFIG_PATH` environment variable).

Example `config.json`:

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

### File Manager Configuration

The file manager configuration can be provided in `file_manager_config.json`. This configuration can be overridden by environment variables.

Example `file_manager_config.json`:

```json
{
  "backends": {
    "local": {
      "enabled": true,
      "base_path": "data/files/local",
      "requires_auth": false
    },
    "git": {
      "enabled": true,
      "base_path": "data/files/git",
      "requires_auth": false,
      "user_name": "OpenManus",
      "user_email": "openmanus@example.com"
    },
    "google_drive": {
      "enabled": true,
      "requires_auth": true,
      "credentials_path": "credentials/google_drive_credentials.json",
      "root_folder": "OpenManus"
    },
    "onedrive": {
      "enabled": false,
      "requires_auth": true,
      "credentials_path": "credentials/onedrive_credentials.json",
      "root_folder": "OpenManus"
    }
  },
  "storage_preferences": {
    "temp": "local",
    "code": "git",
    "knowledge": "git",
    "document": "google_drive",
    "image": "google_drive",
    "video": "google_drive",
    "audio": "google_drive",
    "general": "local"
  }
}
```

## Programmatic Configuration Access

OpenManus provides a `Config` class for accessing configuration values programmatically:

```python
from src.config import load_config

# Load configuration
config = load_config()

# Access configuration values
data_dir = config.get("data_dir", "./data")  # With default fallback
memory_path = config.get_tool_config("memory", "memory_path", "data/memories")

# Set configuration values
config.set("log_level", "DEBUG")
config.set_tool_config("llm", "default_provider", "anthropic")

# Save configuration changes
from src.config import save_config
save_config(config)
```

## Environment Variables Reference

Below is a complete reference of all environment variables supported by OpenManus:

| Variable | Description | Default |
|----------|-------------|---------|
| **Core Settings** | | |
| OPENMANUS_DATA_DIR | Base directory for all data storage | "./data" |
| OPENMANUS_LOG_LEVEL | Logging level (DEBUG, INFO, WARNING, ERROR) | "INFO" |
| OPENMANUS_TEMP_DIR | Directory for temporary files | "./temp" |
| OPENMANUS_CONFIG_PATH | Path to main configuration file | "config.json" |
| **API and Service** | | |
| FRONTEND_PORT | Port for the frontend server | 3000 |
| API_PORT | Port for the API server | 5000 |
| TOOLS_PORT | Port for the tools server | 5001 |
| API_HOST | API host address | "localhost" |
| API_PATH | API path prefix | "api" |
| **LLM Providers** | | |
| DEFAULT_PLANNER_LLM | LLM for planning agent | "gpt4o" |
| DEFAULT_EXECUTOR_LLM | LLM for executor agent | "claude" |
| DEFAULT_TOOLAGENT_LLM | LLM for tool agent | "local" |
| OPENMANUS_DEFAULT_LLM | Default LLM provider | "openai" |
| OPENMANUS_DEFAULT_MODEL | Default model name | "gpt-3.5-turbo" |
| OPENMANUS_MAX_TOKENS | Maximum tokens for responses | 1000 |
| OPENAI_API_KEY | OpenAI API key | None |
| ANTHROPIC_API_KEY | Anthropic API key | None |
| ENABLE_LOCAL_LLM | Enable local LLM | false |
| LOCAL_LLM_PATH | Path to local model | "models/llama3" |
| LOCAL_LLM_API_URL | URL for local LLM API | "http://localhost:8000/v1" |
| **File Storage** | | |
| OPENMANUS_DEFAULT_FILE_BACKEND | Default storage backend | "local" |
| OPENMANUS_FILE_STORAGE_PATH | Path for local file storage | "data/files/local" |
| OPENMANUS_GIT_STORAGE_PATH | Path for git repositories | "data/files/git" |
| OPENMANUS_GIT_USER_NAME | Git user name | "OpenManus" |
| OPENMANUS_GIT_USER_EMAIL | Git user email | "openmanus@example.com" |
| GOOGLE_DRIVE_CLIENT_ID | Google Drive client ID | None |
| GOOGLE_DRIVE_CLIENT_SECRET | Google Drive client secret | None |
| GOOGLE_DRIVE_REDIRECT_URI | Google Drive redirect URI | "http://localhost:8080" |
| OPENMANUS_GDRIVE_TOKEN_PATH | Path to Google Drive token | "credentials/gdrive_token.json" |
| OPENMANUS_GDRIVE_CREDENTIALS_PATH | Path to Google Drive credentials | "credentials/gdrive_credentials.json" |
| OPENMANUS_GDRIVE_ROOT_FOLDER | Google Drive root folder | "OpenManus" |
| OPENMANUS_ONEDRIVE_CREDENTIALS_PATH | Path to OneDrive credentials | "credentials/onedrive_credentials.json" |
| OPENMANUS_ONEDRIVE_ROOT_FOLDER | OneDrive root folder | "OpenManus" |
| OPENMANUS_STORAGE_TEMP | Storage for temporary files | "local" |
| OPENMANUS_STORAGE_CODE | Storage for code files | "git" |
| OPENMANUS_STORAGE_KNOWLEDGE | Storage for knowledge files | "git" |
| OPENMANUS_STORAGE_DOCUMENT | Storage for documents | "google_drive" |
| OPENMANUS_STORAGE_IMAGE | Storage for images | "google_drive" |
| OPENMANUS_STORAGE_VIDEO | Storage for videos | "google_drive" |
| OPENMANUS_STORAGE_AUDIO | Storage for audio files | "google_drive" |
| OPENMANUS_STORAGE_GENERAL | Storage for general files | "local" |
| **Memory Tool** | | |
| OPENMANUS_MEMORY_PATH | Path to memory storage | "data/memories" |
| OPENMANUS_USE_VECTORS | Enable vector search (1/0) | 0 |
| OPENMANUS_MEMORY_BACKUP_ENABLED | Enable automatic backups (1/0) | 1 |
| OPENMANUS_MEMORY_BACKUP_INTERVAL | Minutes between backups | 60 |
| **Vector Database** | | |
| OPENMANUS_VECTOR_DB_PATH | Path to vector database | "data/vectors" |
| OPENMANUS_VECTOR_MODEL | Embedding model name | "all-MiniLM-L6-v2" |
| OPENMANUS_VECTOR_DIMENSION | Embedding dimension | 384 |
| VECTOR_DB_BACKEND | Vector database backend | "faiss" |
| **Code Executor** | | |
| OPENMANUS_CODE_WORKSPACE | Path to code execution workspace | "data/workspace" |
| OPENMANUS_CODE_TIMEOUT | Default timeout in seconds | 5 |
| OPENMANUS_CODE_SANDBOX_TYPE | Sandbox type (docker, subprocess) | "subprocess" |
| **Monitoring** | | |
| OPENMANUS_MONITORING_ENABLED | Enable monitoring (1/0) | 1 |
| OPENMANUS_LOG_PATH | Path to store log files | "data/logs" |
| OPENMANUS_METRICS_PATH | Path to store metrics data | "data/metrics" |
| OPENMANUS_METRICS_SAVE_INTERVAL | Seconds between metrics saves | 300 |
| **Task Decomposition** | | |
| OPENMANUS_TASK_STORAGE_PATH | Path to store task data | "data/tasks" |
| OPENMANUS_TASK_NOTIFICATIONS | Enable task notifications (1/0) | 0 |
| **Document Processing** | | |
| OPENMANUS_DOCUMENT_CACHE_DIR | Path to cache processed documents | "data/document_cache" |
| OPENMANUS_DOCUMENT_ENABLE_OCR | Enable OCR capabilities (1/0) | 0 |
| OPENMANUS_DOCUMENT_ENABLE_ADVANCED | Enable advanced document analysis (1/0) | 0 |
| **Other Tools** | | |
| WEB_BROWSER_API_KEY | API key for web browser tool | None |