# API Documentation Template

## Tool Name

**Description**: A brief description of the tool's purpose and functionality.

**Import Path**: `from src.tools.example_tool import ExampleTool`

**Dependencies**: List of external dependencies (e.g., `faiss-cpu`, `sentence-transformers`, etc.)

## Initialization

```python
tool = ExampleTool(
    param1="value1",  # Description of param1
    param2="value2",  # Description of param2
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| param1 | str | "default" | Detailed description of param1 |
| param2 | int | 100 | Detailed description of param2 |

## Methods

### method_name(param1, param2)

Description of what the method does.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param1 | str | Yes | Description of param1 |
| param2 | Dict[str, Any] | No | Description of param2 |

#### Returns

| Type | Description |
|------|-------------|
| Dict[str, Any] | Description of the return value |

#### Example

```python
result = tool.method_name("example", {"key": "value"})
```

#### Raises

| Exception | Condition |
|-----------|-----------|
| ValueError | When param1 is invalid |
| FileNotFoundError | When the specified file cannot be found |

## Configuration Options

Configuration options can be set via:
- Environment variables
- Configuration file
- Initialization parameters

### Environment Variables

| Variable | Description |
|----------|-------------|
| EXAMPLE_TOOL_PATH | Path to the tool's data directory |

### Configuration File

Configuration can also be provided via a JSON file:

```json
{
  "param1": "value1",
  "param2": 200
}
```

## Examples

For complete examples, see:
- [Basic Usage](/examples/example_tool_usage.py)
- [Advanced Usage](/examples/advanced_example_tool_usage.py)