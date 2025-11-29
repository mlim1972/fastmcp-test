## ADDED Requirements

### Requirement: Dynamic MCP Tool Registration
The system SHALL provide the ability to register MCP tools dynamically at runtime without using the `@mcp.tool` decorator annotation.

#### Scenario: FastAPI to MCP Conversion
- **WHEN** a FastAPI application with REST endpoints is provided
- **THEN** the system SHALL convert all FastAPI endpoints to MCP tools using `FastMCP.from_fastapi()`
- **AND** each REST endpoint SHALL become an invocable MCP tool

#### Scenario: Manual Tool Registration
- **WHEN** a tool function is defined without decorators
- **THEN** the system SHALL support adding it via `mcp.add_tool()` or the constructor `tools` parameter
- **AND** the tool SHALL be discoverable by MCP clients

---

### Requirement: REST API Exposure via MCP
The system SHALL host a REST API and expose its endpoints as MCP tools to MCP clients.

#### Scenario: Item CRUD Operations
- **WHEN** an MCP client calls the `list_items` tool
- **THEN** the system SHALL return all items from the in-memory store
- **AND** the underlying REST API `GET /items` SHALL be invoked

#### Scenario: Item Creation via MCP
- **WHEN** an MCP client calls the `create_item` tool with item data
- **THEN** the system SHALL create a new item via the REST API
- **AND** return the created item with an assigned ID

#### Scenario: Computation Tool
- **WHEN** an MCP client calls the `calculate` tool with operation and operands
- **THEN** the system SHALL perform the requested arithmetic operation
- **AND** return the result

---

### Requirement: Dual-Protocol Server
The system SHALL serve both REST API and MCP protocol from a single server instance.

#### Scenario: REST API Access
- **WHEN** a client sends an HTTP request to `/items`
- **THEN** the system SHALL respond with REST API format (JSON)

#### Scenario: MCP Protocol Access
- **WHEN** an MCP client connects to the `/mcp` endpoint
- **THEN** the system SHALL respond using the MCP protocol
- **AND** list all available tools derived from the REST API

---

### Requirement: Project Structure with UV
The system SHALL use `uv` as the Python package manager and follow modern Python project conventions.

#### Scenario: Project Initialization
- **WHEN** the project is cloned
- **THEN** running `uv sync` SHALL install all dependencies
- **AND** the project SHALL be runnable via `uv run python -m dynamic_mcp.main`

#### Scenario: pyproject.toml Configuration
- **WHEN** examining `pyproject.toml`
- **THEN** it SHALL declare dependencies: fastmcp, fastapi, uvicorn, httpx
- **AND** it SHALL define the package as `dynamic_mcp`

---

### Requirement: Documentation
The system SHALL include comprehensive documentation explaining the dynamic MCP tool pattern.

#### Scenario: README Contents
- **WHEN** a developer reads `README.md`
- **THEN** they SHALL find installation instructions using `uv`
- **AND** instructions for running the server
- **AND** examples of testing both REST API and MCP tools
- **AND** an architecture explanation diagram or description

#### Scenario: Code Comments
- **WHEN** reviewing source code
- **THEN** each module SHALL have a docstring explaining its purpose
- **AND** key FastMCP operations SHALL have inline comments
