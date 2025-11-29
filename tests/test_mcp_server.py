"""
Tests for MCP Server and Dynamic Tool Registration

This module contains tests for verifying:
- Pattern A: FastAPI to MCP conversion
- Pattern B: Programmatic tool registration with add_tool()
- Pattern C: Runtime tool registration without restart

Run tests with:
    uv run pytest tests/ -v
"""

import pytest
import asyncio
from fastmcp import Client
from fastmcp.tools import Tool

from dynamic_mcp.main import (
    create_mcp_server,
    create_external_api_tool,
    ExternalToolConfig,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mcp_server():
    """Create a fresh MCP server for each test."""
    return create_mcp_server()


@pytest.fixture
def external_tool_config():
    """Sample configuration for external API tool."""
    return ExternalToolConfig(
        name="test_external_api",
        description="Test external API tool",
        endpoint_url="https://jsonplaceholder.typicode.com/posts/1",
        http_method="GET",
        tags=["test", "external"],
    )


# =============================================================================
# Pattern A: FastAPI to MCP Conversion Tests
# =============================================================================

class TestFastAPIToMCPConversion:
    """Tests for Pattern A: FastMCP.from_fastapi() conversion."""

    @pytest.mark.asyncio
    async def test_fastapi_endpoints_converted_to_tools(self, mcp_server):
        """Verify that FastAPI endpoints are converted to MCP tools."""
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            
            # FastAPI endpoints should be available as tools
            assert "list_items" in tool_names
            assert "create_item" in tool_names
            assert "get_item" in tool_names
            assert "update_item" in tool_names
            assert "delete_item" in tool_names
            assert "calculate" in tool_names
            assert "health_check" in tool_names

    @pytest.mark.asyncio
    async def test_list_items_tool_returns_items(self, mcp_server):
        """Verify list_items tool returns inventory items."""
        async with Client(mcp_server) as client:
            result = await client.call_tool("list_items", {})
            
            # Should return a list of items
            assert isinstance(result.data, list)
            assert len(result.data) >= 3  # Initial items

    @pytest.mark.asyncio
    async def test_calculate_tool_performs_operations(self, mcp_server):
        """Verify calculate tool performs arithmetic correctly."""
        async with Client(mcp_server) as client:
            # Test addition
            result = await client.call_tool("calculate", {
                "operation": "add",
                "a": 10,
                "b": 5,
            })
            # Result may be a Pydantic object or dict depending on FastMCP version
            data = result.data if isinstance(result.data, dict) else result.data.model_dump() if hasattr(result.data, 'model_dump') else vars(result.data)
            assert data["result"] == 15
            
            # Test multiplication
            result = await client.call_tool("calculate", {
                "operation": "multiply",
                "a": 7,
                "b": 8,
            })
            data = result.data if isinstance(result.data, dict) else result.data.model_dump() if hasattr(result.data, 'model_dump') else vars(result.data)
            assert data["result"] == 56

    @pytest.mark.asyncio
    async def test_create_and_get_item(self, mcp_server):
        """Verify create_item and get_item tools work together."""
        async with Client(mcp_server) as client:
            # Create a new item
            result = await client.call_tool("create_item", {
                "name": "Test Widget",
                "price": 99.99,
                "description": "A test widget",
            })
            
            # Handle Pydantic object or dict response
            data = result.data if isinstance(result.data, dict) else result.data.model_dump() if hasattr(result.data, 'model_dump') else vars(result.data)
            assert data["name"] == "Test Widget"
            assert data["price"] == 99.99
            created_id = data["id"]
            
            # Retrieve the created item
            result = await client.call_tool("get_item", {"item_id": created_id})
            data = result.data if isinstance(result.data, dict) else result.data.model_dump() if hasattr(result.data, 'model_dump') else vars(result.data)
            assert data["name"] == "Test Widget"


# =============================================================================
# Pattern B: Programmatic Tool Registration Tests
# =============================================================================

class TestProgrammaticToolRegistration:
    """Tests for Pattern B: mcp.add_tool() programmatic registration."""

    @pytest.mark.asyncio
    async def test_dynamic_tools_registered(self, mcp_server):
        """Verify dynamically registered tools are available."""
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            
            # Dynamic tools should be registered
            assert "echo" in tool_names
            assert "server_info" in tool_names
            assert "api_reference" in tool_names

    @pytest.mark.asyncio
    async def test_echo_tool_echoes_message(self, mcp_server):
        """Verify echo tool returns the input message."""
        async with Client(mcp_server) as client:
            result = await client.call_tool("echo", {"message": "Hello, MCP!"})
            assert "Hello, MCP!" in str(result.data)

    @pytest.mark.asyncio
    async def test_server_info_tool_returns_metadata(self, mcp_server):
        """Verify server_info tool returns server metadata."""
        async with Client(mcp_server) as client:
            result = await client.call_tool("server_info", {})
            
            assert result.data["name"] == "Dynamic MCP Tools Server"
            assert result.data["version"] == "0.1.0"
            assert "patterns_demonstrated" in result.data


# =============================================================================
# Pattern C: Runtime Tool Registration Tests
# =============================================================================

class TestRuntimeToolRegistration:
    """Tests for Pattern C: Runtime tool registration without restart."""

    def test_external_tool_config_validation(self):
        """Verify ExternalToolConfig validates input correctly."""
        config = ExternalToolConfig(
            name="valid_tool",
            description="A valid tool",
            endpoint_url="https://api.example.com/data",
            http_method="POST",
            tags=["test"],
        )
        
        assert config.name == "valid_tool"
        assert config.http_method == "POST"

    def test_create_external_api_tool_returns_tool(self, external_tool_config):
        """Verify create_external_api_tool creates a valid Tool object."""
        tool = create_external_api_tool(external_tool_config)
        
        assert isinstance(tool, Tool)
        assert tool.name == "test_external_api"
        assert "test" in tool.tags
        assert "external" in tool.tags

    @pytest.mark.asyncio
    async def test_runtime_tool_registration(self, mcp_server, external_tool_config):
        """Verify tools can be registered at runtime."""
        async with Client(mcp_server) as client:
            # Get initial tool count
            initial_tools = await client.list_tools()
            initial_count = len(initial_tools)
            
            # Register a new tool at runtime
            new_tool = create_external_api_tool(external_tool_config)
            mcp_server.add_tool(new_tool)
            
            # Verify tool count increased
            updated_tools = await client.list_tools()
            assert len(updated_tools) == initial_count + 1
            
            # Verify new tool is in the list
            tool_names = [t.name for t in updated_tools]
            assert "test_external_api" in tool_names

    @pytest.mark.asyncio
    async def test_runtime_tool_removal(self, mcp_server, external_tool_config):
        """Verify tools can be removed at runtime."""
        async with Client(mcp_server) as client:
            # Register a tool
            new_tool = create_external_api_tool(external_tool_config)
            mcp_server.add_tool(new_tool)
            
            tools_after_add = await client.list_tools()
            count_after_add = len(tools_after_add)
            
            # Remove the tool
            mcp_server.remove_tool(external_tool_config.name)
            
            # Verify tool count decreased
            tools_after_remove = await client.list_tools()
            assert len(tools_after_remove) == count_after_add - 1
            
            # Verify tool is no longer in list
            tool_names = [t.name for t in tools_after_remove]
            assert external_tool_config.name not in tool_names

    @pytest.mark.asyncio
    async def test_runtime_registered_tool_is_callable(self, mcp_server):
        """Verify dynamically registered tools can be called."""
        async with Client(mcp_server) as client:
            # Register a tool that calls JSONPlaceholder API
            config = ExternalToolConfig(
                name="get_post",
                description="Fetch a post from JSONPlaceholder",
                endpoint_url="https://jsonplaceholder.typicode.com/posts/1",
                http_method="GET",
            )
            tool = create_external_api_tool(config)
            mcp_server.add_tool(tool)
            
            # Call the dynamically registered tool
            result = await client.call_tool("get_post", {})
            
            # Verify it returned data from JSONPlaceholder
            assert result.data["id"] == 1
            assert result.data["userId"] == 1
            assert "title" in result.data
            
            # Cleanup
            mcp_server.remove_tool("get_post")


# =============================================================================
# Tool Count and Server State Tests
# =============================================================================

class TestServerState:
    """Tests for overall server state and tool management."""

    @pytest.mark.asyncio
    async def test_initial_tool_count(self, mcp_server):
        """Verify the expected number of initial tools."""
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            # Should have 10 tools: 7 from FastAPI + 3 from dynamic registration
            assert len(tools) == 10

    @pytest.mark.asyncio
    async def test_tool_descriptions_populated(self, mcp_server):
        """Verify all tools have descriptions for LLMs."""
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            
            for tool in tools:
                assert tool.description, f"Tool {tool.name} missing description"
                assert len(tool.description) > 10, f"Tool {tool.name} has too short description"

    @pytest.mark.asyncio
    async def test_multiple_runtime_registrations(self, mcp_server):
        """Verify multiple tools can be registered at runtime."""
        async with Client(mcp_server) as client:
            initial_tools = await client.list_tools()
            initial_count = len(initial_tools)
            
            # Register multiple tools
            for i in range(3):
                config = ExternalToolConfig(
                    name=f"test_tool_{i}",
                    description=f"Test tool number {i}",
                    endpoint_url=f"https://jsonplaceholder.typicode.com/posts/{i+1}",
                    http_method="GET",
                )
                tool = create_external_api_tool(config)
                mcp_server.add_tool(tool)
            
            # Verify all were added
            updated_tools = await client.list_tools()
            assert len(updated_tools) == initial_count + 3
            
            # Cleanup
            for i in range(3):
                mcp_server.remove_tool(f"test_tool_{i}")
