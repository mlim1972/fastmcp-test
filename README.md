# FastMCP Dynamic Tools - Proof of Concept

This project demonstrates how to create MCP (Model Context Protocol) server tools **dynamically** without using the `@mcp.tool` decorator annotation. It showcases how to expose existing REST APIs as MCP tools, enabling AI assistants like Claude to interact with your APIs through a standardized protocol.

## 🎯 Key Concepts

### What This PoC Demonstrates

1. **Pattern A: FastAPI to MCP Conversion** - Automatically convert REST endpoints to MCP tools using `FastMCP.from_fastapi()`
2. **Pattern B: Programmatic Tool Registration** - Add tools using `Tool.from_function()` and `mcp.add_tool()` for custom scenarios
3. **Pattern C: Runtime Tool Registration** - Add/remove tools while the server is running, without restart
4. **Dual-Protocol Server** - Serve both REST API and MCP protocol from a single server

### Why Dynamic Tools?

- **Existing APIs**: Expose your existing REST APIs to AI assistants without rewriting them
- **Runtime Configuration**: Load tool definitions from config files or databases
- **API Discovery**: Generate tools from OpenAPI specs or API discovery mechanisms
- **Hot Reload**: Add new tools at runtime without server restart
- **Flexibility**: Mix auto-converted and custom tools in the same server

## 📁 Project Structure

```
.
├── pyproject.toml              # Project configuration and dependencies
├── README.md                   # This file
├── AGENTS.md                   # Instructions for AI coding assistants
├── src/
│   └── dynamic_mcp/
│       ├── __init__.py         # Package initialization
│       ├── main.py             # Server entry point (dual-protocol + runtime registration)
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py       # FastAPI REST endpoints
│       └── tools/
│           ├── __init__.py
│           └── dynamic.py      # Dynamic tool registration helpers
└── tests/
    ├── __init__.py
    ├── test_mcp_server.py      # MCP server and tool tests
    ├── test_rest_api.py        # REST API endpoint tests
    └── test_runtime_registration.py  # Runtime tool management tests
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone and navigate to the project directory
git clone <repository-url>
cd fastmcp-test

# Install dependencies with uv
uv sync
```

### Running the Server

#### HTTP Mode (Dual-Protocol)

This mode serves both REST API and MCP protocol:

```bash
# Default: http://127.0.0.1:8000
uv run python -m dynamic_mcp.main

# Custom host and port
uv run python -m dynamic_mcp.main --host 0.0.0.0 --port 9000
```

Once running, you can access:
- **REST API**: `http://localhost:8000/items`
- **API Docs**: `http://localhost:8000/docs`
- **MCP Endpoint**: `http://localhost:8000/mcp`
- **Tool Management**: `http://localhost:8000/tools`

#### STDIO Mode (for Claude Desktop)

This mode runs MCP over standard input/output for integration with Claude Desktop:

```bash
uv run python -m dynamic_mcp.main --mode stdio
```

## 🔧 Architecture

### Pattern A: FastAPI to MCP Conversion

The primary pattern uses `FastMCP.from_fastapi()` to automatically convert FastAPI endpoints:

```python
from fastapi import FastAPI
from fastmcp import FastMCP

# Your existing FastAPI app
app = FastAPI()

@app.get("/items")
def list_items():
    """List all items."""  # This docstring becomes the tool description
    return [...]

# Convert to MCP server - all endpoints become tools
mcp = FastMCP.from_fastapi(app=app, name="My API Server")
```

### Pattern B: Programmatic Tool Registration

For more control, use `Tool.from_function()` and `mcp.add_tool()`:

```python
from fastmcp import FastMCP
from fastmcp.tools import Tool

mcp = FastMCP(name="My Server")

def my_custom_tool(input: str) -> str:
    """This becomes the tool description."""
    return f"Processed: {input}"

# Create a Tool object from the function, then register it
tool = Tool.from_function(
    my_custom_tool,
    name="custom_tool",           # Optional custom name
    description="Custom desc",    # Optional override
    tags={"category", "type"},    # Optional tags
)
mcp.add_tool(tool)
```

> **Important**: `add_tool()` expects a `Tool` object, not a raw function. Use `Tool.from_function()` to wrap your function first.

### Pattern C: Runtime Tool Registration

Add tools dynamically while the server is running:

```python
from fastmcp.tools import Tool

# Create tool at runtime
def new_api_caller():
    """Call an external API."""
    # ... implementation
    pass

tool = Tool.from_function(new_api_caller, name="new_tool", description="...")

# Register without restart - MCP clients are notified automatically
mcp.add_tool(tool)

# Remove tool at runtime
mcp.remove_tool("new_tool")
```

**Key insight**: FastMCP's `add_tool()` and `remove_tool()` modify the internal tool registry in place. MCP clients automatically receive `notifications/tools/list_changed` when tools change.

### Dual-Protocol Server

The server mounts MCP into FastAPI for unified access:

```python
from fastapi import FastAPI
from fastmcp import FastMCP

# Create MCP server from FastAPI app
mcp = FastMCP.from_fastapi(app=api_app)
mcp_app = mcp.http_app(path="/mcp")

# Combine routes
combined = FastAPI(
    routes=[*mcp_app.routes, *api_app.routes],
    lifespan=mcp_app.lifespan,
)
```

## 📡 Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test files
uv run pytest tests/test_mcp_server.py -v
uv run pytest tests/test_rest_api.py -v
uv run pytest tests/test_runtime_registration.py -v

# Run with coverage
uv run pytest tests/ --cov=src/dynamic_mcp
```

### Manual REST API Testing

```bash
# List all items
curl http://localhost:8000/items

# Get a specific item
curl http://localhost:8000/items/1

# Create an item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "New Item", "price": 19.99}'

# Calculate
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{"operation": "add", "a": 10, "b": 5}'
```

### Runtime Tool Registration Testing

```bash
# List current tools
curl http://localhost:8000/tools/

# Register a new tool pointing to external API
curl -X POST http://localhost:8000/tools/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_todos",
    "description": "Fetch todos from JSONPlaceholder API",
    "endpoint_url": "https://jsonplaceholder.typicode.com/todos/1",
    "http_method": "GET",
    "tags": ["external", "demo"]
  }'

# Verify tool was added
curl http://localhost:8000/tools/

# Unregister the tool
curl -X DELETE http://localhost:8000/tools/unregister/get_todos
```

### MCP Client Example

```python
import asyncio
from fastmcp import Client

async def test_mcp():
    # Connect to the MCP server
    async with Client("http://localhost:8000/mcp") as client:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Call a tool
        result = await client.call_tool("list_items", {})
        print(f"\nItems: {result}")
        
        # Create an item
        result = await client.call_tool(
            "create_item",
            {"name": "Test Item", "price": 29.99}
        )
        print(f"\nCreated: {result}")

asyncio.run(test_mcp())
```

## 🔌 Claude Desktop Integration

Add this to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "dynamic-tools": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/fastmcp-test",
        "run",
        "python",
        "-m",
        "dynamic_mcp.main",
        "--mode",
        "stdio"
      ]
    }
  }
}
```

## 📋 Available Tools

When connected, the MCP server exposes these tools:

| Tool | Description | Source |
|------|-------------|--------|
| `list_items` | List all items in inventory | FastAPI endpoint (Pattern A) |
| `get_item` | Get item by ID | FastAPI endpoint (Pattern A) |
| `create_item` | Create a new item | FastAPI endpoint (Pattern A) |
| `update_item` | Update an existing item | FastAPI endpoint (Pattern A) |
| `delete_item` | Delete an item | FastAPI endpoint (Pattern A) |
| `calculate` | Perform arithmetic operations | FastAPI endpoint (Pattern A) |
| `health_check` | Check server health | FastAPI endpoint (Pattern A) |
| `echo` | Echo back a message | Dynamic registration (Pattern B) |
| `server_info` | Get server information | Dynamic registration (Pattern B) |
| `api_reference` | Get REST API reference | Dynamic registration (Pattern B) |
| *dynamic* | Tools registered at runtime | Runtime registration (Pattern C) |

## 🔑 Key Takeaways

### Technical Findings

1. **`add_tool()` expects Tool objects**: Use `Tool.from_function(fn, name=..., description=...)` to wrap functions before registering
2. **Docstrings Matter**: Endpoint/function docstrings become tool descriptions for LLMs
3. **Type Hints Required**: FastMCP uses type hints to generate tool schemas
4. **Runtime Registration Works**: `mcp.add_tool()` and `mcp.remove_tool()` work without restart
5. **Client Notification**: MCP clients are automatically notified of tool changes via `notifications/tools/list_changed`

### Architecture Patterns

1. **Dual-Protocol**: Serve REST and MCP from the same server for flexibility
2. **Global Server Reference**: Store the MCP server globally for runtime tool management
3. **External API Wrapping**: Create MCP tools that proxy to external REST APIs
4. **Combined Lifespan**: Use MCP's lifespan manager for proper startup/shutdown

### Common Pitfalls Avoided

- ❌ `mcp.add_tool(my_function)` - Wrong! Expects Tool object
- ✅ `mcp.add_tool(Tool.from_function(my_function, ...))` - Correct!

## 📚 References

- [FastMCP Documentation](https://gofastmcp.com/getting-started/welcome)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Specification](https://modelcontextprotocol.io/)
- [uv Documentation](https://docs.astral.sh/uv/)

## 📄 License

MIT License - See LICENSE file for details.
