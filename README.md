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
git clone https://github.com/henryalps/OpenManus.git
cd OpenManus
```

### 2. Build and Run with Docker
```bash
# Build and start all containers
docker-compose up --build
```

This will launch:
- Backend container with the multi-agent system and integrated tools
- Frontend container serving the Next.js web interface
- API server for task delegation and execution

### 3. Test the System
Once running, you can interact with OpenManus via:
- CLI: Use the provided Python client
- API: Send requests to http://localhost:5000 (see API docs below)
- Web UI: Access http://localhost:3000

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
```

### Project Structure
```
OpenManus/
├── docker/               # Docker configurations
│   ├── frontend/        # Next.js frontend container
│   │   └── Dockerfile   # Frontend container configuration
│   └── unified/         # Backend container configuration
│       ├── Dockerfile   # Backend container configuration
│       └── start.sh     # Container startup script
├── src/                 # Source code
│   ├── agents/          # Multi-agent logic (Python)
│   ├── tools/           # Tool implementations
│   ├── client.py        # CLI client for testing
│   └── server.py        # Main API server
├── docs/                # Documentation and API specs
├── package.json         # Next.js frontend dependencies
├── next.config.js       # Next.js configuration
├── docker-compose.yml   # Docker Compose configuration
└── README.md           # This file
```

### Configuration

1. **Copy the example environment file:**
```bash
cp .env.example .env
```

2. **Edit the `.env` file to configure your LLM providers:**
```bash
# OpenAI settings
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic settings
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Local LLM settings (optional)
ENABLE_LOCAL_LLM=true
LOCAL_LLM_PATH=models/llama3
```

3. **Edit the `docker-compose.yml` file to customize:**
```yaml
services:
  backend:
    build: 
      context: .
      dockerfile: docker/unified/Dockerfile
    ports:
      - "5000:5000"  # API port
    env_file:
      - .env
    environment:
      - WEB_BROWSER_API_KEY=your_key_here
    volumes:
      - ./src:/app/src
      - ./data:/app/data

  frontend:
    build:
      context: .
      dockerfile: docker/frontend/Dockerfile
    ports:
      - "3000:3000"  # Web UI port
    depends_on:
      - backend
```

### API Documentation
The agent server exposes a REST API at http://localhost:5000. Key endpoints:

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
- Implement core multi-agent coordination.
- Add support for GAIA benchmark tasks.
- Integrate advanced NLP models (e.g., LLaMA, Grok).
- Enhance toolset with real-time web scraping and visualization.
- Release v1.0 with stable task execution.

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