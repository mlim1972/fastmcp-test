"""
Dynamic Tool Registration

This module demonstrates Pattern B: Programmatic MCP tool registration
using mcp.add_tool() instead of the @mcp.tool decorator.

This pattern is useful when:
- Tools are defined at runtime based on configuration
- Tools need to be loaded from external sources
- You want to create tools that wrap external APIs
- Tool definitions come from a database or API discovery

The key insight is that MCP tools are just functions with metadata.
FastMCP's Tool.from_function() lets you create Tool objects from functions,
and add_tool() registers them with the server.
"""

from fastmcp import FastMCP
from fastmcp.tools import Tool


def register_dynamic_tools(mcp: FastMCP) -> None:
    """
    Register dynamically created tools with the MCP server.
    
    This function demonstrates several ways to add tools programmatically:
    1. Adding a regular function as a tool
    2. Adding tools with custom names and descriptions
    3. Adding tools with tags for organization
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    
    # =========================================================================
    # Example 1: Simple function as a tool
    # =========================================================================
    
    def echo(message: str) -> str:
        """
        Echo back the provided message.
        
        This is a simple demonstration tool that returns whatever
        message is passed to it. Useful for testing MCP connectivity.
        
        Args:
            message: The message to echo back.
            
        Returns:
            The same message that was provided.
        """
        return f"Echo: {message}"
    
    # Add the function as a tool using Tool.from_function() and add_tool()
    # Tool.from_function() wraps the function with metadata, then add_tool() registers it
    echo_tool = Tool.from_function(
        echo,
        name="echo",  # Tool name (optional, defaults to function name)
        description="Echo back the provided message. Useful for testing MCP connectivity.",
        tags={"utility", "test"},
    )
    mcp.add_tool(echo_tool)
    
    # =========================================================================
    # Example 2: Tool with custom metadata
    # =========================================================================
    
    def get_server_info() -> dict:
        """Get information about the MCP server."""
        return {
            "name": "Dynamic MCP Tools Server",
            "version": "0.1.0",
            "description": "A PoC demonstrating dynamic MCP tool registration",
            "patterns_demonstrated": [
                "FastMCP.from_fastapi() - Convert FastAPI to MCP tools",
                "mcp.add_tool() - Programmatic tool registration",
            ],
        }
    
    # You can customize tool metadata when creating the Tool object
    server_info_tool = Tool.from_function(
        get_server_info,
        name="server_info",  # Custom name
        description="Get detailed information about this MCP server and the patterns it demonstrates.",
        tags={"info", "metadata"},  # Tags for organization
    )
    mcp.add_tool(server_info_tool)
    
    # =========================================================================
    # Example 3: Tool that demonstrates external API reference
    # =========================================================================
    
    def api_reference() -> dict:
        """
        Get information about the REST API endpoints exposed via MCP.
        
        This tool helps users understand that the MCP tools correspond
        to REST API endpoints, and provides information about how to
        access them directly via HTTP if needed.
        """
        return {
            "message": "This MCP server exposes REST API endpoints as tools.",
            "rest_api_base_url": "http://localhost:8000",
            "endpoints": [
                {
                    "tool_name": "list_items",
                    "rest_endpoint": "GET /items",
                    "description": "List all items in the inventory",
                },
                {
                    "tool_name": "get_item", 
                    "rest_endpoint": "GET /items/{item_id}",
                    "description": "Get a specific item by ID",
                },
                {
                    "tool_name": "create_item",
                    "rest_endpoint": "POST /items",
                    "description": "Create a new item",
                },
                {
                    "tool_name": "update_item",
                    "rest_endpoint": "PUT /items/{item_id}",
                    "description": "Update an existing item",
                },
                {
                    "tool_name": "delete_item",
                    "rest_endpoint": "DELETE /items/{item_id}",
                    "description": "Delete an item",
                },
                {
                    "tool_name": "calculate",
                    "rest_endpoint": "POST /calculate",
                    "description": "Perform arithmetic calculations",
                },
            ],
            "note": "All tools call the corresponding REST endpoints internally.",
        }
    
    api_reference_tool = Tool.from_function(
        api_reference,
        name="api_reference",
        description="Get a mapping of MCP tools to their corresponding REST API endpoints.",
        tags={"info", "api"},
    )
    mcp.add_tool(api_reference_tool)


def create_tool_from_config(config: dict) -> callable:
    """
    Factory function to create tools from configuration.
    
    This demonstrates how you might create tools dynamically based on
    configuration loaded from a file, database, or API discovery.
    
    Args:
        config: A dictionary with tool configuration:
            - name: The tool name
            - description: The tool description
            - operation: What the tool does
            
    Returns:
        A callable that can be registered as an MCP tool.
        
    Example:
        config = {
            "name": "greet",
            "description": "Greet a user by name",
            "prefix": "Hello",
        }
        tool_fn = create_tool_from_config(config)
        mcp.add_tool(tool_fn, name=config["name"])
    """
    prefix = config.get("prefix", "Result")
    
    def dynamic_tool(input_value: str) -> str:
        """A dynamically created tool."""
        return f"{prefix}: {input_value}"
    
    # Update the docstring dynamically
    dynamic_tool.__doc__ = config.get("description", "A dynamic tool")
    dynamic_tool.__name__ = config.get("name", "dynamic_tool")
    
    return dynamic_tool
