<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

---

# FastMCP Dynamic Tools - AI Agent Instructions

This document provides instructions and findings for AI coding assistants working on this FastMCP dynamic tools proof-of-concept project.

## Project Overview

This is a **Proof of Concept (PoC)** demonstrating dynamic MCP tool registration without using the `@mcp.tool` decorator. The project uses:

- **FastMCP 2.x** - MCP server library
- **FastAPI** - REST API framework
- **uv** - Python package manager
- **Python 3.10+**

## Key Files

| File | Purpose |
|------|---------|
| `src/dynamic_mcp/main.py` | Main server with dual-protocol support and runtime tool registration |
| `src/dynamic_mcp/api/routes.py` | FastAPI REST endpoints (converted to MCP tools) |
| `src/dynamic_mcp/tools/dynamic.py` | Pattern B demonstration - programmatic tool registration |
| `pyproject.toml` | Project dependencies and configuration |
| `tests/test_*.py` | Comprehensive test suite |

## Three Patterns for Dynamic Tool Registration

### Pattern A: FastAPI to MCP Conversion

```python
from fastmcp import FastMCP
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
def list_items():
    """This docstring becomes the tool description."""
    return [...]

# Automatic conversion - all endpoints become MCP tools
mcp = FastMCP.from_fastapi(app=app, name="Server Name")
```

### Pattern B: Programmatic Registration with add_tool()

**⚠️ CRITICAL**: `add_tool()` expects a `Tool` object, NOT a raw function!

```python
# ❌ WRONG - This will fail
mcp.add_tool(my_function)

# ✅ CORRECT - Wrap function with Tool.from_function() first
from fastmcp.tools import Tool

tool = Tool.from_function(
    my_function,
    name="tool_name",
    description="Tool description for LLMs",
    tags={"category", "type"},  # Optional
)
mcp.add_tool(tool)
```

### Pattern C: Runtime Tool Registration (Without Restart)

Tools can be added/removed while the server is running:

```python
# Store global MCP server reference
_mcp_server: FastMCP | None = None

def create_mcp_server() -> FastMCP:
    global _mcp_server
    mcp = FastMCP.from_fastapi(app=api_app, name="Server")
    _mcp_server = mcp
    return mcp

# Later, at runtime:
new_tool = Tool.from_function(fn, name="new_tool", description="...")
_mcp_server.add_tool(new_tool)  # Added without restart!

# Remove tool:
_mcp_server.remove_tool("new_tool")  # Removed without restart!
```

**Key insight**: MCP clients are automatically notified via `notifications/tools/list_changed`.

## Common Pitfalls & Solutions

### 1. add_tool() TypeError

**Problem**: `TypeError: add_tool() expects Tool object`

**Cause**: Passing a raw function instead of a Tool object

**Solution**:
```python
from fastmcp.tools import Tool
tool = Tool.from_function(fn, name="...", description="...")
mcp.add_tool(tool)
```

### 2. Tool Descriptions Missing

**Problem**: MCP clients show empty descriptions

**Cause**: Missing or poor docstrings

**Solution**: Always add descriptive docstrings to functions - they become tool descriptions

### 3. Type Hints Missing

**Problem**: Tool schemas not generated correctly

**Cause**: FastMCP requires type hints to generate JSON schemas

**Solution**: Always use full type hints on function parameters and return types

### 4. Dual-Protocol Lifespan Issues

**Problem**: Server crashes on startup/shutdown

**Cause**: Not using MCP's lifespan manager

**Solution**:
```python
mcp_app = mcp.http_app(path="/mcp")

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    async with mcp_app.lifespan(app):
        yield

combined = FastAPI(
    routes=[*mcp_app.routes, *api_app.routes],
    lifespan=combined_lifespan,
)
```

## Running & Testing

### Start the Server

```bash
# HTTP mode (REST + MCP)
uv run python -m dynamic_mcp.main

# STDIO mode (for Claude Desktop)
uv run python -m dynamic_mcp.main --mode stdio
```

### Run Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_mcp_server.py -v
```

### Manual Testing

```bash
# List tools via REST
curl http://localhost:8000/tools/

# Register a tool at runtime
curl -X POST http://localhost:8000/tools/register \
  -H "Content-Type: application/json" \
  -d '{"name": "my_tool", "description": "...", "endpoint_url": "https://...", "http_method": "GET"}'

# MCP client test
uv run python -c "
import asyncio
from fastmcp import Client

async def test():
    async with Client('http://localhost:8000/mcp') as client:
        tools = await client.list_tools()
        print([t.name for t in tools])
        
asyncio.run(test())
"
```

## Architecture Decisions

1. **Dual-Protocol Server**: Single server serves REST (/) and MCP (/mcp) for flexibility
2. **Global Server Reference**: `_mcp_server` global allows runtime tool management
3. **External API Wrapping**: Pattern C creates MCP tools that proxy to external REST APIs
4. **In-Memory Registry**: `_external_tools` dict tracks dynamically registered tools

## Dependencies

```toml
[project]
dependencies = [
    "fastmcp>=2.0.0",    # MCP server library
    "fastapi>=0.115.0",  # REST API framework
    "uvicorn>=0.32.0",   # ASGI server
    "httpx>=0.28.0",     # Async HTTP client
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",  # For async test support
]
```

## When Modifying This Project

1. **Adding new REST endpoints**: Add to `src/dynamic_mcp/api/routes.py` - they auto-convert to MCP tools
2. **Adding custom tools**: Use Pattern B in `src/dynamic_mcp/tools/dynamic.py`
3. **Runtime registration**: Use the `/tools/register` endpoint or modify `main.py`
4. **Tests**: Add tests to appropriate file in `tests/`

## Project Status

This is a **completed PoC** demonstrating:
- ✅ Pattern A: FastAPI to MCP conversion
- ✅ Pattern B: Programmatic tool registration
- ✅ Pattern C: Runtime tool registration
- ✅ Dual-protocol server
- ✅ Comprehensive test suite
- ✅ Full documentation

## References

- [FastMCP Docs](https://gofastmcp.com)
- [MCP Specification](https://modelcontextprotocol.io)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [uv Docs](https://docs.astral.sh/uv)