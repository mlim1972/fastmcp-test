## 1. Project Setup
- [x] 1.1 Initialize Python project with `uv init`
- [x] 1.2 Create `pyproject.toml` with dependencies (fastmcp, fastapi, uvicorn, httpx)
- [x] 1.3 Create source directory structure (`src/dynamic_mcp/`)
- [x] 1.4 Create `README.md` with project overview and usage instructions

## 2. REST API Implementation
- [x] 2.1 Create FastAPI application in `src/dynamic_mcp/api/routes.py`
- [x] 2.2 Implement Item model (Pydantic) with id, name, description, price fields
- [x] 2.3 Implement CRUD endpoints: GET /items, GET /items/{id}, POST /items, PUT /items/{id}, DELETE /items/{id}
- [x] 2.4 Implement a computation endpoint: POST /calculate (simple arithmetic operations)
- [x] 2.5 Add comprehensive docstrings to all endpoints (these become tool descriptions)

## 3. Dynamic MCP Tool Registration
- [x] 3.1 Create main server entry point in `src/dynamic_mcp/main.py`
- [x] 3.2 Implement Pattern A: Use `FastMCP.from_fastapi()` to convert FastAPI app to MCP server
- [x] 3.3 Implement Pattern B: Create helper in `src/dynamic_mcp/tools/dynamic.py` showing manual `add_tool()` usage
- [x] 3.4 Mount MCP server into FastAPI app for dual-protocol access
- [x] 3.5 Add tool metadata/descriptions that reference the underlying REST endpoints

## 4. Documentation and Comments
- [x] 4.1 Add module-level docstrings explaining the purpose of each file
- [x] 4.2 Add inline comments explaining key FastMCP concepts
- [x] 4.3 Update README.md with:
  - Installation instructions using `uv`
  - How to run the server
  - How to test MCP tools (using fastmcp client or Claude Desktop)
  - Architecture explanation
  - Example curl commands for REST API
- [x] 4.4 Add example MCP client code in README.md

## 5. Validation
- [x] 5.1 Test that REST API endpoints work via curl/httpie
- [x] 5.2 Test that MCP tools are discoverable via `list_tools`
- [x] 5.3 Test that MCP tool calls work correctly
- [x] 5.4 Verify all code has appropriate comments
