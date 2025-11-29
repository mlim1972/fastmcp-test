"""
Dynamic MCP Tools - Proof of Concept

This package demonstrates how to create MCP server tools dynamically
without using the @mcp.tool decorator annotation. It shows how to:

1. Convert FastAPI endpoints to MCP tools using FastMCP.from_fastapi()
2. Programmatically register tools using mcp.add_tool()
3. Serve both REST API and MCP protocol from a single server

For more information, see the README.md file.
"""

__version__ = "0.1.0"
