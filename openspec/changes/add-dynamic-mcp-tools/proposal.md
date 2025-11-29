# Change: Add Dynamic MCP Tools PoC with FastMCP

## Why
We need a Proof of Concept (PoC) to demonstrate how to create MCP server tools dynamically without using the `@mcp.tool` decorator annotation. The goal is to explore creating dynamic MCP tools that inform client MCP applications about REST APIs they should use, rather than implementing tool logic directly in the MCP server.

This enables scenarios where:
- MCP tools are generated based on existing/external REST APIs
- Tool definitions can be loaded from configuration or discovered at runtime
- The MCP server acts as a "bridge" or "registry" for existing API capabilities

## What Changes
- Create a new Python project using `uv` as the package manager
- Implement a FastMCP-based MCP server that:
  - Hosts a REST API (using FastAPI) with sample endpoints
  - Dynamically registers MCP tools that expose the REST API to MCP clients
  - Uses `FastMCP.from_openapi()` or `mcp.add_tool()` for programmatic tool registration
- Include proper documentation (README.md) and code comments
- Set up `pyproject.toml` with all necessary dependencies

## Impact
- New project structure created at workspace root
- Affected code: New Python package with FastMCP, FastAPI, and uvicorn dependencies
- This is a PoC/greenfield project with no existing specs or code to modify
