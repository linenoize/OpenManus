# OpenManus

<p align="center">
  <img src="docs/logo.png" alt="OpenManus Logo">
</p>

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-supported-green.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![JavaScript](https://img.shields.io/badge/javascript-ES6+-yellow.svg)

## Overview

OpenManus is an open-source project aimed at replicating the capabilities of the Manus AI agent, a groundbreaking general-purpose AI developed by Monica. Manus is known for its ability to autonomously execute complex tasks—ranging from personalized travel planning to stock analysis—surpassing models like GPT-4 on the GAIA benchmark. OpenManus seeks to bring these capabilities to the open-source community using a modular, containerized framework built with Docker, Python, and JavaScript.

This repository provides a starting point for developers and researchers to build, deploy, and experiment with a multi-agent AI system. Our goal is to create a flexible and extensible platform that mirrors Manus's autonomous task execution while fostering community contributions.

## Features

- **Multi-Agent System**: Collaborative AI agents working together to solve complex tasks.
- **Dockerized Environment**: Easy setup and deployment with containerization.
- **Task Execution**: Supports tasks like travel planning, data analysis, and content generation.
- **Tool Integration**: Web browsing, code execution, and data retrieval capabilities.
- **Memory System**: Persistent memory across sessions with namespaces, search, and metadata.
- **Vector Database**: Semantic search with multiple backends (FAISS, ChromaDB, Milvus) and sentence embeddings for intelligent retrieval.
- **Modular Design**: Easily extendable with new agents, tools, or features.
- **Multiple LLM Support**: Integration with OpenAI (GPT-4o), Anthropic (Claude), and local models.
- **LLM Preference System**: Customize which LLM to use for specific agents and tools.
- **Community-Driven**: Open to contributions and enhancements.

## Prerequisites

Before you begin, ensure you have the following installed:
- [Docker](https://docs.docker.com/get-docker/) (version 20.10 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 1.29 or higher)
- [Node.js](https://nodejs.org/) (version 20.18 or higher, for local development)
- [Python](https://python.org/) (version 3.9 or higher, for local development)
- Git (for cloning and contributing)

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/linenoize/OpenManus.git
cd OpenManus
```

### 2. Install Dependencies (for local development)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install JavaScript dependencies for the frontend
npm install
```

### 3. Build and Run with Docker
```bash
# Run with separate containers (standard setup)
docker-compose up --build

# OR use unified container (all services in one container)
docker-compose -f docker-compose.unified.yml up --build

# OR use development mode with hot-reloading
docker-compose -f docker-compose.dev.yml up --build
```

This will launch:
- Backend container with the multi-agent system and integrated tools
- Frontend container serving the Next.js web interface
- API server for task delegation and execution

The unified container option simplifies deployment by running all services in a single container with Nginx as a reverse proxy (exposed on port 80).

### 4. Configure the Environment
OpenManus uses a dual configuration approach with environment variables stored in a `.env` file and additional settings in `config.json`:

1. Copy or create the example environment file:
```bash
cp .env.example .env
```

2. Edit the `.env` file to configure (add this to your .gitignore):
   - LLM provider API keys (OpenAI, Anthropic)
   - Port configurations 
   - Vector database options
   - Storage backend settings

3. Create a `config.json` file (add this to your .gitignore as well):
```json
{
  "llm_preferences": {
    "default_planner_llm": "gpt4o",
    "default_executor_llm": "claude",
    "default_toolagent_llm": "gpt4o"
  },
  "vector_db": {
    "backend": "faiss",
    "embedding_model": "all-MiniLM-L6-v2"
  },
  "logging": {
    "level": "INFO",
    "file": "data/logs/openmanus.log"
  }
}
```

Complete `.env` template:
```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
ENABLE_LOCAL_LLM=false
LOCAL_LLM_PATH=models/mistral-7b
API_PORT=5010
TOOLS_PORT=5011
FRONTEND_PORT=3010
VECTOR_DB_BACKEND=faiss  # Options: faiss, chroma, milvus, openai
OPENMANUS_CONFIG_PATH=config.json
FILE_MANAGER_CONFIG_PATH=file_manager_config.json
OPENMANUS_STORAGE_TEMP=local
OPENMANUS_STORAGE_CODE=git
OPENMANUS_STORAGE_DOCUMENT=local
```

> Note: Make sure to add both `.env` and `config.json` to your `.gitignore` file to avoid committing sensitive API keys to your repository.

4. **Vector Embedding Setup:**
   
   The vector database components are installed automatically when using Docker. They include:
   
   - **FAISS**: High-performance similarity search library (installed via `faiss-cpu`)
   - **Sentence Transformers**: Text embedding models like `all-MiniLM-L6-v2` (downloaded on first use)
   - **OpenAI Vector Store**: Cloud-based vector database using OpenAI's infrastructure (requires API key)
   - **ChromaDB** and **Milvus**: Optional alternative vector database backends
   
   For local development, install these dependencies manually:
   
   ```bash
   pip install faiss-cpu sentence-transformers
   # OpenAI backend (recommended)
   pip install openai>=1.0.0
   # Other optional backends
   pip install chromadb pymilvus
   ```
   
   **Vector Database Backend Selection:**
   You can select your preferred vector database backend by setting the `VECTOR_DB_BACKEND` environment variable:
   
   ```bash
   # In your .env file
   VECTOR_DB_BACKEND=faiss  # Default local backend
   # OR
   VECTOR_DB_BACKEND=openai  # Cloud-based OpenAI backend
   ```
   
   The system supports these backends:
   - **faiss**: Fast local vector search (default, recommended for most use cases)
   - **openai**: OpenAI's managed vector database (requires API key)
   - **chroma**: Local persistent vector database (optional)
   - **milvus**: Scalable vector database server (optional)
   
   If you choose the OpenAI backend, make sure your OpenAI API key is set:
   ```bash
   OPENAI_API_KEY=your_key_here
   ```

   The first time you use the vector database with a local backend (FAISS, ChromaDB), the embedding model will be downloaded automatically from Hugging Face (approximately 90MB).

For full configuration documentation, see `docs/configuration.md`.

### 5. Test the System
Once running, you can interact with OpenManus via:
- CLI: Use the provided Python client
- API: Send requests to http://localhost/api (when using unified container) or http://localhost:5000 (standard setup)
- Web UI: Access http://localhost (when using unified container) or http://localhost:3000 (standard setup)

Example CLI commands:
```bash
# Execute a task
python src/client.py task --task "Plan a 3-day trip to Tokyo"

# Check system status and available LLM providers
python src/client.py status

# List available LLM providers and their capabilities
python src/client.py llm list

# Get current LLM preferences for agents and tools
python src/client.py llm recommendations 

# Set Claude as the preferred provider for the planner agent
python src/client.py llm preference --type agent --name planner --provider claude --reason "Better at creative planning"

# Memory operations
python src/client.py memory list  # List all memory namespaces
python src/client.py memory store --namespace research --content "Tesla announced a new product" --metadata '{"source": "news", "date": "2024-03-15"}'
python src/client.py memory get-all --namespace research  # Get all memories in the research namespace
python src/client.py memory search --namespace research --query "Tesla"  # Search for memories

# Vector database (semantic search) examples
python examples/vector_db_usage.py  # Run the vector database demo
# Try the example with your own queries to see semantic search in action

# Use different vector database backends
# Edit requirements.txt to uncomment the desired backend, then:
pip install -e .  # Install with the selected backends
python examples/vector_db_usage.py  # Will now show available backends
```

### Project Structure
```
OpenManus/
├── docker/               # Docker configurations
│   ├── frontend/        # Next.js frontend container
│   │   └── Dockerfile   # Frontend container configuration
│   ├── unified/         # Backend container configuration
│   │   ├── Dockerfile   # Backend container configuration
│   │   └── start.sh     # Container startup script
│   └── unified-all/     # Unified container (all services)
│       ├── Dockerfile   # Multi-stage build for all services
│       ├── start.sh     # Unified startup script
│       ├── nginx.conf   # Nginx reverse proxy configuration
│       └── dev/         # Development mode configuration
├── src/                 # Source code
│   ├── agents/          # Multi-agent logic (Python)
│   ├── tools/           # Tool implementations
│   │   ├── file_manager.py     # File management tool
│   │   ├── memory_tool.py      # Memory storage and retrieval
│   │   ├── vector_db_tool.py   # Vector database with multiple backends
│   │   └── ...
│   ├── client.py        # CLI client for testing
│   └── server.py        # Main API server
├── examples/            # Example usage scripts
├── docs/                # Documentation and API specs
├── package.json         # Next.js frontend dependencies
├── next.config.js       # Next.js configuration
├── docker-compose.yml   # Standard Docker Compose configuration
├── docker-compose.unified.yml # Unified container configuration
├── docker-compose.dev.yml # Development mode configuration
└── README.md           # This file
```

### Configuration

1. **Creating Required Configuration Files:**

   You need to set up two main configuration files:

   - `.env`: Environment variables and API keys
   - `config.json`: System preferences and settings

   Both files should be added to your `.gitignore` to keep credentials secure.

2. **Docker Architecture:**

   OpenManus can run in two primary configurations:
   
   - **Standard setup** (docker-compose.yml): Three separate containers for API, tools, and frontend
   - **Unified setup** (docker-compose.unified.yml): Single container with Nginx reverse proxy

3. **Port Customization:**

   To customize ports (e.g., API on 5010, tools on 5011, frontend on 3010):

   ```yaml
   # In docker-compose.yml
   services:
     unified:
       ports:
         - "5010:5000"  # Map container port 5000 to host port 5010
         - "5011:5001"  # Map container port 5001 to host port 5011
     
     frontend:
       ports:
         - "3010:3000"  # Map container port 3000 to host port 3010
   ```

   And update your `.env`:
   ```
   API_PORT=5010
   TOOLS_PORT=5011
   FRONTEND_PORT=3010
   ```

4. **Web Server Configuration (Apache):**

   To expose OpenManus through Apache with HTTPS:

   ```apache
   <VirtualHost *:80>
       ServerName openmanus.site.com
       Redirect permanent / https://openmanus.site.com/
   </VirtualHost>

   <VirtualHost *:443>
       ServerName openmanus.site.com
       
       SSLEngine on
       SSLCertificateFile /path/to/certificate.crt
       SSLCertificateKeyFile /path/to/private.key
       
       # Frontend proxy
       ProxyPass / http://localhost:3010/
       ProxyPassReverse / http://localhost:3010/
       
       # API proxy
       ProxyPass /api http://localhost:5010/
       ProxyPassReverse /api http://localhost:5010/
       
       # Tools proxy
       ProxyPass /tools http://localhost:5011/
       ProxyPassReverse /tools http://localhost:5011/
       
       ErrorLog ${APACHE_LOG_DIR}/openmanus_error.log
       CustomLog ${APACHE_LOG_DIR}/openmanus_access.log combined
   </VirtualHost>
   ```

   Enable required Apache modules:
   ```bash
   sudo a2enmod proxy proxy_http ssl
   sudo systemctl restart apache2
   ```

### API Documentation
The agent server exposes a REST API at http://localhost/api (when using unified container) or http://localhost:5000 (standard setup). Key endpoints:

**POST /task**: Submit a task for execution.
```json
Body: { "task": "Analyze Tesla stock trends" }
Response: { "status": "success", "result": "..." }
```

**GET /status**: Check system health and available LLM providers.
```json
Response: { 
  "status": "running",
  "llm_providers": ["gpt4o", "claude", "local"]
}
```

**GET /llm/providers**: List all available LLM providers with capabilities.
```json
Response: {
  "providers": [
    {
      "name": "gpt4o",
      "capabilities": {
        "type": "openai",
        "coding": 5,
        "reasoning": 5,
        "creativity": 4,
        "knowledge": 5,
        "context_length": 128000,
        "latency": "medium",
        "privacy": "low",
        "cost": "high"
      }
    },
    ...
  ]
}
```

**GET /memory**: List all memory namespaces.
```json
Response: {
  "namespaces": ["general", "research", "user_preferences"]
}
```

**GET /memory/{namespace}**: Get all memories in a namespace.
```json
Response: {
  "memories": [
    {
      "id": "2024-03-15T14:30:45.123456",
      "content": "Tesla announced a new product",
      "timestamp": "2024-03-15T14:30:45.123456",
      "metadata": {
        "source": "news",
        "date": "2024-03-15"
      }
    },
    ...
  ]
}
```

**POST /memory/{namespace}**: Store a new memory.
```json
Body: {
  "content": "Important information to remember",
  "metadata": {"source": "user", "importance": "high"},
  "memory_id": "custom-id-123" // optional
}
Response: {
  "status": "success",
  "memory": {
    "id": "custom-id-123",
    "content": "Important information to remember",
    "timestamp": "2024-03-15T14:30:45.123456",
    "metadata": {"source": "user", "importance": "high"}
  }
}
```

**GET /vector-db/collections**: List all vector collections.
```json
Response: {
  "collections": ["research", "knowledge_base", "user_data"]
}
```

**POST /vector-db/collections/{collection_name}/documents**: Add a document to a vector collection.
```json
Body: {
  "text": "The Transformer architecture has revolutionized NLP",
  "metadata": {"topic": "AI", "source": "research paper"},
  "external_id": "doc123" // optional
}
Response: {
  "status": "success",
  "id": "doc123"
}
```

**GET /vector-db/collections/{collection_name}/search**: Semantic search in a vector collection.
```json
Query parameters:
  - query: The search query
  - k: Number of results to return (default: 5)
  
Response: {
  "results": [
    {
      "id": "doc123",
      "text": "The Transformer architecture has revolutionized NLP",
      "metadata": {"topic": "AI", "source": "research paper"},
      "timestamp": "2024-03-15T14:30:45.123456",
      "similarity": 0.92,
      "backend": "faiss"  // The backend used for this vector search
    },
    ...
  ]
}
```

**GET /llm/recommendations**: Get current LLM recommendations for agents and tools.
```json
Response: {
  "providers": [...],
  "agent_preferences": {
    "planner": {
      "provider": "gpt4o",
      "reason": "GPT-4o is well-suited for complex planning tasks requiring reasoning"
    },
    ...
  },
  "tool_preferences": {...}
}
```

**POST /llm/preference**: Set LLM preference for a specific agent or tool.
```json
Body: {
  "entity_type": "agent",  // "agent" or "tool"
  "entity_name": "planner",  // agent or tool name 
  "provider_name": "claude",  // LLM provider name
  "reason": "Better at breaking down complex tasks"  // optional
}
Response: { "status": "success" }
```

Full API docs are available in `docs/api.md`.

### Contributing
We welcome contributions! To get started:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to your branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

Please read `CONTRIBUTING.md` for guidelines.

### Roadmap
- ✅ Implement core multi-agent coordination
- ✅ Add persistent memory system for context retention
- ✅ Add vector embedding database for semantic search
- ✅ Add multiple vector database backends (FAISS, ChromaDB, Milvus)
- ✅ Implement file management system with multiple storage options
- Add support for GAIA benchmark tasks
- Integrate advanced NLP models (e.g., LLaMA, Grok)
- Enhance toolset with:
  - Real-time web scraping and visualization
  - ✅ Document processing capabilities 
  - Advanced RAG (Retrieval Augmented Generation) capabilities
  - ✅ Structured data tool for CSV/JSON/database operations
  - ✅ Metadata extraction tool for various file types
  - ✅ Task decomposition tool for complex requests
- Release v1.0 with stable task execution

### Inspiration
OpenManus is inspired by:
- The official Manus project (manus.im).
- The open-Manus community effort (GitHub).
- GAIA benchmark for general AI assistants (arXiv).

### License
This project is licensed under the MIT License. See `LICENSE` for details.

### Contact
For questions or collaboration, reach out via GitHub Issues or email [henryalps@gmail.com](mailto:henryalps@gmail.com).

Happy coding! Let's build the future of AI agents together!