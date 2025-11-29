"""
Main Server Entry Point

This module creates a dual-protocol server that serves:
1. REST API endpoints at /items, /calculate, etc.
2. MCP protocol at /mcp

It demonstrates two patterns for dynamic MCP tool registration:
- Pattern A: Using FastMCP.from_fastapi() to convert FastAPI endpoints to MCP tools
- Pattern B: Using mcp.add_tool() for programmatic tool registration
- Pattern C: Runtime tool registration via REST API (tools added while server runs)

The server can be run in different modes:
- HTTP mode (default): Serves both REST and MCP over HTTP
- STDIO mode: For direct MCP client connections (e.g., Claude Desktop)
"""

import argparse
import sys
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
from fastmcp.tools import Tool
from pydantic import BaseModel, Field

from dynamic_mcp.api.routes import app as api_app
from dynamic_mcp.tools.dynamic import register_dynamic_tools


# =============================================================================
# Global MCP Server Reference (for runtime tool registration)
# =============================================================================

# This global reference allows us to add tools at runtime while the server runs
_mcp_server: FastMCP | None = None


def get_mcp_server() -> FastMCP:
    """Get the global MCP server instance."""
    if _mcp_server is None:
        raise RuntimeError("MCP server not initialized")
    return _mcp_server


# =============================================================================
# Create MCP Server from FastAPI App
# =============================================================================

def create_mcp_server() -> FastMCP:
    """
    Create an MCP server by converting the FastAPI app.
    
    This demonstrates Pattern A: Using FastMCP.from_fastapi() to automatically
    convert all FastAPI endpoints into MCP tools. The endpoint docstrings
    become tool descriptions, and the Pydantic models define the tool schemas.
    
    Returns:
        FastMCP: The configured MCP server with tools from the FastAPI app.
    """
    global _mcp_server
    
    # Convert FastAPI app to MCP server
    # This automatically creates MCP tools from all FastAPI endpoints
    mcp = FastMCP.from_fastapi(
        app=api_app,
        name="Dynamic MCP Tools Server",
    )
    
    # Register additional dynamic tools (Pattern B demonstration)
    # These tools are added programmatically using add_tool()
    register_dynamic_tools(mcp)
    
    # Store global reference for runtime tool registration
    _mcp_server = mcp
    
    return mcp


# =============================================================================
# Runtime Tool Registration API (Pattern C)
# =============================================================================

class ExternalToolConfig(BaseModel):
    """Configuration for registering an external REST API as an MCP tool."""
    name: str = Field(..., description="Unique name for the MCP tool")
    description: str = Field(..., description="Description shown to MCP clients")
    endpoint_url: str = Field(..., description="The REST API endpoint URL to call")
    http_method: str = Field(default="GET", description="HTTP method (GET, POST, etc.)")
    tags: list[str] = Field(default=[], description="Optional tags for organization")


# In-memory registry of dynamically registered external tools
_external_tools: dict[str, ExternalToolConfig] = {}


def create_external_api_tool(config: ExternalToolConfig) -> Tool:
    """
    Create an MCP tool that wraps an external REST API endpoint.
    
    This demonstrates Pattern C: Runtime tool registration that points
    MCP clients to external REST APIs without implementing the logic locally.
    
    Args:
        config: Configuration for the external API tool.
        
    Returns:
        Tool: A FastMCP Tool that can be registered with the server.
    """
    import httpx
    
    async def call_external_api(params: dict[str, Any] | None = None) -> dict:
        """
        Call the external REST API endpoint.
        
        Args:
            params: Optional parameters to pass to the API.
            
        Returns:
            The JSON response from the external API.
        """
        async with httpx.AsyncClient() as client:
            if config.http_method.upper() == "GET":
                response = await client.get(config.endpoint_url, params=params)
            elif config.http_method.upper() == "POST":
                response = await client.post(config.endpoint_url, json=params)
            elif config.http_method.upper() == "PUT":
                response = await client.put(config.endpoint_url, json=params)
            elif config.http_method.upper() == "DELETE":
                response = await client.delete(config.endpoint_url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {config.http_method}")
            
            response.raise_for_status()
            return response.json()
    
    # Update function metadata for better tool descriptions
    call_external_api.__doc__ = f"{config.description}\n\nCalls: {config.http_method} {config.endpoint_url}"
    call_external_api.__name__ = config.name
    
    return Tool.from_function(
        call_external_api,
        name=config.name,
        description=config.description,
        tags=set(config.tags) if config.tags else None,
    )


# FastAPI router for runtime tool management
from fastapi import APIRouter
tools_router = APIRouter(prefix="/tools", tags=["Tool Management"])


@tools_router.get("/")
def list_registered_tools() -> dict:
    """
    List all currently registered MCP tools.
    
    Returns both built-in tools and dynamically registered external tools.
    """
    mcp = get_mcp_server()
    tools = list(mcp._tool_manager._tools.keys())
    return {
        "total_tools": len(tools),
        "tools": tools,
        "external_tools": list(_external_tools.keys()),
    }


@tools_router.post("/register")
def register_external_tool(config: ExternalToolConfig) -> dict:
    """
    Register a new external REST API as an MCP tool AT RUNTIME.
    
    This endpoint allows you to dynamically add new MCP tools while
    the server is running, without any restart required.
    
    The registered tool will immediately be available to MCP clients.
    FastMCP automatically sends `notifications/tools/list_changed`
    to connected clients so they can refresh their tool list.
    
    Args:
        config: The external tool configuration.
        
    Returns:
        Confirmation of the registered tool.
    """
    mcp = get_mcp_server()
    
    # Check if tool already exists
    if config.name in mcp._tool_manager._tools:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{config.name}' already exists"
        )
    
    # Create and register the tool
    tool = create_external_api_tool(config)
    mcp.add_tool(tool)
    
    # Store in our registry
    _external_tools[config.name] = config
    
    return {
        "status": "success",
        "message": f"Tool '{config.name}' registered successfully",
        "tool": {
            "name": config.name,
            "description": config.description,
            "endpoint": config.endpoint_url,
            "method": config.http_method,
        }
    }


@tools_router.delete("/unregister/{tool_name}")
def unregister_tool(tool_name: str) -> dict:
    """
    Remove a dynamically registered tool AT RUNTIME.
    
    Args:
        tool_name: The name of the tool to remove.
        
    Returns:
        Confirmation of the removal.
    """
    mcp = get_mcp_server()
    
    if tool_name not in _external_tools:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' is not a dynamically registered external tool"
        )
    
    # Remove from MCP server
    mcp.remove_tool(tool_name)
    
    # Remove from our registry
    del _external_tools[tool_name]
    
    return {
        "status": "success",
        "message": f"Tool '{tool_name}' removed successfully"
    }


# =============================================================================
# Create Combined App (Dual-Protocol)
# =============================================================================

def create_combined_app() -> FastAPI:
    """
    Create a combined FastAPI app that serves both REST and MCP protocols.
    
    This mounts the MCP server into the FastAPI app, allowing:
    - REST API access at /items, /calculate, etc.
    - MCP protocol access at /mcp
    
    Returns:
        FastAPI: The combined app serving both protocols.
    """
    # Create the MCP server
    mcp = create_mcp_server()
    
    # Create the MCP ASGI app with the /mcp path
    mcp_app = mcp.http_app(path="/mcp")
    
    # Create combined app with MCP lifespan
    # The lifespan manager ensures proper startup/shutdown of the MCP server
    @asynccontextmanager
    async def combined_lifespan(app: FastAPI):
        """Manage lifecycle of both FastAPI and MCP servers."""
        async with mcp_app.lifespan(app):
            yield
    
    # Create the combined FastAPI app
    combined_app = FastAPI(
        title="Dynamic MCP Tools - Dual Protocol Server",
        description=(
            "This server provides both REST API and MCP protocol access. "
            "REST endpoints are available at /items, /calculate, etc. "
            "MCP protocol is available at /mcp. "
            "Use /tools/register to add new MCP tools at runtime!"
        ),
        version="0.1.0",
        routes=[
            *mcp_app.routes,  # MCP routes (at /mcp)
            *api_app.routes,  # Original API routes
        ],
        lifespan=combined_lifespan,
    )
    
    # Include the tools management router for runtime tool registration
    combined_app.include_router(tools_router)
    
    return combined_app


# =============================================================================
# Entry Points
# =============================================================================

def run_http_server(host: str = "127.0.0.1", port: int = 8000):
    """
    Run the server in HTTP mode (dual-protocol).
    
    Args:
        host: The host to bind to.
        port: The port to bind to.
    """
    import uvicorn
    
    print(f"Starting dual-protocol server at http://{host}:{port}")
    print(f"  REST API: http://{host}:{port}/items")
    print(f"  MCP endpoint: http://{host}:{port}/mcp")
    print(f"  Tool Management: http://{host}:{port}/tools")
    print(f"  API docs: http://{host}:{port}/docs")
    
    app = create_combined_app()
    uvicorn.run(app, host=host, port=port)


def run_stdio_server():
    """
    Run the server in STDIO mode for direct MCP client connections.
    
    This mode is used when connecting from MCP clients like Claude Desktop
    that communicate over standard input/output.
    """
    mcp = create_mcp_server()
    print("Starting MCP server in STDIO mode...", file=sys.stderr)
    mcp.run(transport="stdio")


def main():
    """
    Main entry point with command-line argument parsing.
    
    Supports two modes:
    - http (default): Dual-protocol server over HTTP
    - stdio: MCP-only server over STDIO
    """
    parser = argparse.ArgumentParser(
        description="Dynamic MCP Tools Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run HTTP server (default)
  python -m dynamic_mcp.main
  
  # Run HTTP server on custom port
  python -m dynamic_mcp.main --port 9000
  
  # Run STDIO server for Claude Desktop
  python -m dynamic_mcp.main --mode stdio
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["http", "stdio"],
        default="http",
        help="Server mode: 'http' for dual-protocol HTTP server, 'stdio' for MCP over STDIO",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (HTTP mode only)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (HTTP mode only)",
    )
    
    args = parser.parse_args()
    
    if args.mode == "stdio":
        run_stdio_server()
    else:
        run_http_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
