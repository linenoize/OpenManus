# OpenManus Architecture

## Overview

OpenManus is a multi-agent system with pluggable tools and LLM service integration. The architecture follows a coordinator pattern where a central component manages task distribution among specialized agents and tools.

## Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      OpenManus System                           │
│                                                                 │
│  ┌─────────────────┐                                            │
│  │                 │    manages    ┌──────────────────────┐     │
│  │ TaskCoordinator ├───────────────┤   ExecutionAgent    │     │
│  │                 │               └──────────────────────┘     │
│  └─────────┬───────┘                                            │
│            │                                                    │
│            │ manages                                            │
│            ▼                                                    │
│  ┌─────────────────┐                                            │
│  │                 │               ┌──────────────────────┐     │
│  │    ToolAgent    ├───────────────┤         Tools       │     │
│  │                 │     uses      │                     │     │
│  └─────────────────┘               │  ┌────────────────┐ │     │
│                                    │  │  FileManager   │ │     │
│  ┌─────────────────┐               │  ├────────────────┤ │     │
│  │                 │               │  │ MemoryTool     │ │     │
│  │   LLM Service   │               │  ├────────────────┤ │     │
│  │                 ├─────────┐     │  │ VectorDBTool   │ │     │
│  └─────────────────┘         │     │  ├────────────────┤ │     │
│                              │     │  │ CodeExecutor   │ │     │
│                              │     │  ├────────────────┤ │     │
│                              └─────┼──┤ DataRetriever  │ │     │
│                         used by    │  ├────────────────┤ │     │
│                                    │  │ WebBrowser     │ │     │
│                                    │  ├────────────────┤ │     │
│                                    │  │ MonitoringTool │ │     │
│                                    │  └────────────────┘ │     │
│                                    └──────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Coordinator Layer

1. **TaskCoordinator**: Central orchestration component that:
   - Receives task requests
   - Plans task execution using LLM service
   - Delegates execution to appropriate agents
   - Manages error handling and recovery
   - Collects results and formats responses

2. **ExecutionAgent**: Handles execution of complex multi-step tasks
   - Breaks down tasks into logical steps
   - Executes steps in sequence
   - Reports progress to coordinator
   - Handles errors at the step level

3. **ToolAgent**: Manages direct tool operations
   - Validates tool operation parameters
   - Executes specific tool functions
   - Formats and returns results
   - Handles tool-specific errors

### Tool Layer

OpenManus provides a range of specialized tools for different operations:

1. **FileManagerTool**: File system operations with multiple storage backends
   - Local filesystem
   - Git repositories
   - Google Drive
   - (Future: OneDrive)

2. **MemoryTool**: Persistent memory system for contextual information
   - Stores and retrieves memories with metadata
   - Vector-based semantic search
   - Text-based keyword search
   - Memory chunking for long texts

3. **VectorDBTool**: Vector database for semantic similarity operations
   - Creates and manages collections
   - Generates embeddings from text
   - Provides similarity search
   - Manages persistence of vectors and metadata

4. **CodeExecutor**: Safe execution environment for code
   - Supports multiple languages
   - Sandboxed execution
   - Code validation
   - Result formatting

5. **DataRetriever**: Retrieves data from various sources
   - Structured data parsing
   - API integration
   - Data transformation

6. **WebBrowser**: Web browsing and content extraction
   - Page fetching
   - Content extraction
   - Form submission

7. **MonitoringTool**: System-wide metrics and monitoring
   - Tool usage metrics
   - LLM service metrics
   - Performance tracking
   - Persistent metrics storage

### Service Layer

1. **LLM Service**: Abstraction over LLM providers
   - Provider selection (OpenAI, Claude, local models)
   - Request formatting
   - Response parsing
   - Error handling and retries
   - Token counting

## Data Flow

1. **Task Execution Flow**:
   - Client submits task request
   - Coordinator analyzes task and creates execution plan
   - Plan is executed by ExecutionAgent
   - Each step may involve one or more Tool operations via ToolAgent
   - Results are collected and formatted
   - Response is returned to client

2. **Tool Operation Flow**:
   - ToolAgent receives operation request
   - Parameters are validated
   - Tool method is executed
   - Results are captured and formatted
   - Monitoring metrics are updated
   - Response is returned to agent

3. **LLM Interaction Flow**:
   - LLM Service receives prompt request
   - Provider is selected based on configuration
   - Request is formatted for selected provider
   - Request is sent to provider
   - Response is received and parsed
   - Response is returned to caller

## Integration Points

1. **Client Integration**:
   - REST API via server.py
   - Python client via client.py
   - Direct library usage for Python applications

2. **Tool Integration**:
   - All tools implement a common interface
   - New tools can be registered with the system
   - Tools can be enabled/disabled via configuration

3. **LLM Provider Integration**:
   - Providers implement a common interface
   - Configuration-based provider selection
   - Parameter mapping for different providers

## Configuration

Configuration can be provided via:
1. Environment variables
2. Configuration files (JSON/YAML)
3. Programmatic API parameters

Key configuration areas:
- Storage paths for each tool
- LLM provider credentials
- Performance parameters
- Monitoring options
- Storage backend selection

## Error Handling

The system implements multiple layers of error handling:
1. Tool-level validation and error detection
2. Agent-level error handling and recovery
3. Coordinator-level planning and execution errors
4. Service-level provider failures and retries
5. Structured error responses with context

## Monitoring and Telemetry

The MonitoringTool provides comprehensive metrics:
1. System-wide metrics (requests, errors, tasks)
2. Tool-specific metrics (calls, durations, errors)
3. LLM usage metrics (tokens, latency, success rates)
4. Persistent metrics storage
5. Real-time metrics retrieval