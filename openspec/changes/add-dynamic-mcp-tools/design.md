## Context

FastMCP provides multiple approaches for creating MCP tools dynamically:
1. **`FastMCP.from_openapi()`** - Convert OpenAPI specs to MCP tools automatically
2. **`FastMCP.from_fastapi()`** - Convert FastAPI endpoints to MCP tools
3. **`mcp.add_tool()`** - Programmatically add tool functions at runtime
4. **Constructor `tools` parameter** - Pass a list of tools when creating the server

The PoC will demonstrate two primary patterns:
- **Pattern A**: FastAPI app converted to MCP server (tools call local endpoints)
- **Pattern B**: Dynamic tool registration that informs clients about external REST APIs

## Goals / Non-Goals
- **Goals**:
  - Demonstrate dynamic MCP tool registration without decorators
  - Create a REST API that the MCP server exposes as tools
  - Show how MCP clients can discover and use REST-based tools
  - Use `uv` for Python project management
  - Provide clear documentation and code comments

- **Non-Goals**:
  - Production-ready authentication/authorization
  - Complex error handling or retry logic
  - Integration with external real-world APIs
  - Performance optimization or load testing

## Decisions

### Decision 1: Use FastMCP's `from_fastapi()` as Primary Pattern
- **Why**: This approach directly converts FastAPI endpoints to MCP tools, demonstrating the cleanest path from REST API to MCP tools
- **Alternatives considered**:
  - `from_openapi()` - Requires generating/loading OpenAPI spec first
  - Manual `add_tool()` - More flexible but more boilerplate
- **Chosen approach**: Use `from_fastapi()` for the main demo, with a secondary example showing manual `add_tool()` for custom scenarios

### Decision 2: Single Server Architecture (Dual-Protocol)
- **Why**: FastMCP allows mounting MCP endpoints into FastAPI, enabling both REST and MCP access from the same server
- **Benefit**: Simpler deployment, single port, demonstrates the integration pattern clearly

### Decision 3: Project Structure
```
.
├── pyproject.toml
├── README.md
├── src/
│   └── dynamic_mcp/
│       ├── __init__.py
│       ├── main.py           # Combined server entry point
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py     # REST API endpoints
│       └── tools/
│           ├── __init__.py
│           └── dynamic.py    # Dynamic tool registration helpers
└── tests/
    └── __init__.py
```

### Decision 4: Sample API Domain
- **Choice**: Simple "Item" CRUD API (create, read, update, delete items)
- **Why**: Universal, easy to understand, demonstrates all HTTP methods
- **Bonus**: Will add a computation tool (e.g., calculator) to show variety

## Risks / Trade-offs
- **Risk**: FastMCP version changes may affect API
  - **Mitigation**: Pin FastMCP version in dependencies, document version used
- **Risk**: Dual-protocol server may confuse users about when to use REST vs MCP
  - **Mitigation**: Clear README documentation explaining use cases

## Migration Plan
N/A - This is a greenfield PoC project

## Open Questions
1. Should we also demonstrate the `from_openapi()` approach in a separate example file?
   - **Recommended**: Yes, as a secondary example to show flexibility
2. Should the MCP server include tool descriptions that reference the REST endpoints explicitly?
   - **Recommended**: Yes, this helps demonstrate the "MCP as API registry" concept
