# OpenManus API Documentation

This document provides detailed API documentation for all OpenManus tools and components.

## Table of Contents

- [Memory Tool](#memory-tool)
- [Vector Database Tool](#vector-database-tool)
- [File Manager Tool](#file-manager-tool)
- [Code Executor](#code-executor)
- [LLM Service](#llm-service)
- [Monitoring Tool](#monitoring-tool)
- [Task Coordinator](#task-coordinator)

## Memory Tool

**Description**: Persistent memory system for storing and retrieving information with metadata. Supports both vector-based semantic search and traditional text search.

**Import Path**: `from src.tools.memory_tool import MemoryTool`

**Dependencies**: 
- `faiss-cpu` or `faiss-gpu` (for vector search)
- `sentence-transformers` (for embeddings)
- `nltk` (for text chunking)

### Initialization

```python
memory = MemoryTool(
    memory_path="data/memories",    # Path to store memories
    use_vectors=True,               # Enable vector-based search
    vector_db_path="data/vectors",  # Path for vector database
    model_name="all-MiniLM-L6-v2",  # Embedding model
    chunk_size=512,                 # Text chunk size for long documents
    chunk_overlap=50                # Overlap between chunks
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| memory_path | str | "data/memories" | Directory path to store memory data |
| use_vectors | bool | False | Enable vector-based search |
| vector_db_path | str | "data/vectors" | Directory for vector database storage |
| model_name | str | "all-MiniLM-L6-v2" | SentenceTransformer model for embeddings |
| chunk_size | int | 512 | Size of text chunks for long documents |
| chunk_overlap | int | 50 | Overlap between adjacent chunks |
| backup_enabled | bool | True | Enable automatic backups |
| backup_interval | int | 60 | Minutes between backups |

### Methods

#### store(content, metadata=None, namespace="default", memory_id=None)

Store information in memory.

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| content | str | Yes | The text content to store |
| metadata | Dict[str, Any] | No | Additional metadata to associate with the memory |
| namespace | str | No | Organizational namespace for the memory |
| memory_id | str | No | Custom ID for the memory (auto-generated if None) |

##### Returns

| Type | Description |
|------|-------------|
| str | The memory ID |

##### Example

```python
memory_id = memory.store(
    content="User prefers vegetarian food",
    metadata={"type": "preference", "category": "food"},
    namespace="user_data"
)
```

#### get(memory_id, namespace="default")

Retrieve a specific memory by ID.

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| memory_id | str | Yes | The ID of the memory to retrieve |
| namespace | str | No | The namespace where the memory is stored |

##### Returns

| Type | Description |
|------|-------------|
| Dict[str, Any] | The memory data including content and metadata |

##### Example

```python
memory_data = memory.get("mem_12345", namespace="user_data")
print(memory_data["content"])
print(memory_data["metadata"])
```

#### search(query, namespace="default", k=5, use_vectors=None)

Search for relevant memories.

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | str | Yes | The search query |
| namespace | str | No | The namespace to search in |
| k | int | No | Number of results to return |
| use_vectors | bool | No | Override default vector search setting |

##### Returns

| Type | Description |
|------|-------------|
| List[Dict[str, Any]] | List of matching memories with relevance scores |

##### Example

```python
results = memory.search(
    query="user food preferences",
    namespace="user_data",
    k=3
)

for result in results:
    print(f"Match: {result['content']} (Score: {result['relevance_score']})")
```

#### update(memory_id, content=None, metadata=None, namespace="default")

Update an existing memory.

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| memory_id | str | Yes | The ID of the memory to update |
| content | str | No | New content (None to keep existing) |
| metadata | Dict[str, Any] | No | Metadata to update (merged with existing) |
| namespace | str | No | The namespace where the memory is stored |

##### Returns

| Type | Description |
|------|-------------|
| bool | Success status |

##### Example

```python
success = memory.update(
    memory_id="mem_12345",
    metadata={"last_confirmed": "2023-09-15"},
    namespace="user_data"
)
```

#### delete(memory_id, namespace="default")

Delete a memory.

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| memory_id | str | Yes | The ID of the memory to delete |
| namespace | str | No | The namespace where the memory is stored |

##### Returns

| Type | Description |
|------|-------------|
| bool | Success status |

##### Example

```python
success = memory.delete("mem_12345", namespace="user_data")
```

#### clear_namespace(namespace)

Clear all memories in a namespace.

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| namespace | str | Yes | The namespace to clear |

##### Returns

| Type | Description |
|------|-------------|
| bool | Success status |

##### Example

```python
memory.clear_namespace("temporary_data")
```

#### list_namespaces()

List all available namespaces.

##### Returns

| Type | Description |
|------|-------------|
| List[str] | List of namespace names |

##### Example

```python
namespaces = memory.list_namespaces()
print(f"Available namespaces: {namespaces}")
```

### Configuration Options

Configuration options can be set via:
- Environment variables
- Initialization parameters

#### Environment Variables

| Variable | Description |
|----------|-------------|
| OPENMANUS_MEMORY_PATH | Path to the memory storage directory |
| OPENMANUS_VECTOR_DB_PATH | Path to the vector database directory |
| OPENMANUS_USE_VECTORS | Enable/disable vector search (1/0) |

## Vector Database Tool

**Description**: Tool for vector database storage and retrieval, providing semantic search capabilities using vector embeddings.

**Import Path**: `from src.tools.vector_db_tool import VectorDBTool`

**Dependencies**:
- `faiss-cpu` or `faiss-gpu` 
- `sentence-transformers`
- `numpy`

### Initialization

```python
vector_db = VectorDBTool(
    base_path="data/vectors",        # Path to store vector indices
    model_name="all-MiniLM-L6-v2",   # SentenceTransformer model
    dimension=384                     # Embedding dimension
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| base_path | str | "data/vectors" | Directory to store vector indices and metadata |
| model_name | str | "all-MiniLM-L6-v2" | SentenceTransformer model for embeddings |
| dimension | int | 384 | Embedding dimension (depends on the model) |

### Methods

#### create_collection(collection_name)

Create a new vector collection.

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| collection_name | str | Yes | Name of the collection |

##### Returns

| Type | Description |
|------|-------------|
| bool | True if created successfully, False if already exists |

##### Example

```python
vector_db.create_collection("product_descriptions")
```

#### add_text(collection_name, text, metadata=None, external_id=None)

Add text to a collection.

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| collection_name | str | Yes | Name of the collection |
| text | str | Yes | Text to add |
| metadata | Dict[str, Any] | No | Optional metadata |
| external_id | str | No | Optional external ID |

##### Returns

| Type | Description |
|------|-------------|
| str or None | ID of the added document, or None if failed |

##### Example

```python
doc_id = vector_db.add_text(
    collection_name="product_descriptions",
    text="Wireless headphones with noise cancellation",
    metadata={"category": "electronics", "price": 99.99}
)
```

#### search(collection_name, query, k=5)

Search for similar documents.

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| collection_name | str | Yes | Name of the collection |
| query | str | Yes | Query text |
| k | int | No | Number of results to return |

##### Returns

| Type | Description |
|------|-------------|
| List[Dict[str, Any]] | List of documents with similarity scores |

##### Example

```python
results = vector_db.search(
    collection_name="product_descriptions",
    query="wireless earbuds",
    k=3
)

for result in results:
    print(f"Match: {result['text']} (Score: {result['similarity']})")
```

For detailed information on all tools, including FileManagerTool, CodeExecutor, LLMService, MonitoringTool, and more, please see the individual API documentation files in the docs directory:

- [Memory Tool Documentation](./api/memory_tool.md)
- [Vector Database Documentation](./api/vector_db_tool.md)
- [File Manager Documentation](./api/file_manager.md)
- [Code Executor Documentation](./api/code_executor.md)
- [LLM Service Documentation](./api/llm_service.md)
- [Monitoring Tool Documentation](./api/monitoring.md)
- [Task Coordinator Documentation](./api/coordinator.md)