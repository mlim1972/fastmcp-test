"""
Tests for Runtime Tool Registration via REST API

This module tests the Pattern C: Runtime tool registration feature
where tools can be added/removed via REST endpoints while the server
is running, without requiring a restart.

Run tests with:
    uv run pytest tests/test_runtime_registration.py -v
"""

import pytest
from fastapi.testclient import TestClient

from dynamic_mcp.main import (
    create_combined_app,
    _external_tools,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create a test client for the combined app."""
    app = create_combined_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_external_tools():
    """Clean up external tools registry after each test."""
    yield
    _external_tools.clear()


# =============================================================================
# Tool Management Endpoint Tests
# =============================================================================

class TestToolManagementEndpoints:
    """Tests for /tools REST API endpoints."""

    def test_list_tools_endpoint(self, client):
        """Verify /tools endpoint lists all registered tools."""
        response = client.get("/tools/")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_tools" in data
        assert "tools" in data
        assert "external_tools" in data
        assert data["total_tools"] == 10  # Initial tool count

    def test_register_external_tool(self, client):
        """Verify POST /tools/register adds a new tool."""
        config = {
            "name": "test_api_tool",
            "description": "Test API tool",
            "endpoint_url": "https://jsonplaceholder.typicode.com/posts/1",
            "http_method": "GET",
            "tags": ["test"],
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "test_api_tool" in data["message"]

    def test_tool_count_increases_after_registration(self, client):
        """Verify tool count increases after registration."""
        # Get initial count
        initial = client.get("/tools/").json()
        initial_count = initial["total_tools"]
        
        # Register a tool
        config = {
            "name": "new_tool",
            "description": "A new tool",
            "endpoint_url": "https://api.example.com/data",
            "http_method": "GET",
        }
        client.post("/tools/register", json=config)
        
        # Check count increased
        updated = client.get("/tools/").json()
        assert updated["total_tools"] == initial_count + 1
        assert "new_tool" in updated["tools"]
        assert "new_tool" in updated["external_tools"]

    def test_register_duplicate_tool_fails(self, client):
        """Verify registering a duplicate tool name returns error."""
        config = {
            "name": "duplicate_tool",
            "description": "First tool",
            "endpoint_url": "https://api.example.com/first",
            "http_method": "GET",
        }
        
        # First registration should succeed
        response = client.post("/tools/register", json=config)
        assert response.status_code == 200
        
        # Second registration should fail
        response = client.post("/tools/register", json=config)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_unregister_tool(self, client):
        """Verify DELETE /tools/unregister removes a tool."""
        # First register a tool
        config = {
            "name": "tool_to_remove",
            "description": "This will be removed",
            "endpoint_url": "https://api.example.com/temp",
            "http_method": "GET",
        }
        client.post("/tools/register", json=config)
        
        # Verify it exists
        tools = client.get("/tools/").json()
        assert "tool_to_remove" in tools["tools"]
        
        # Unregister it
        response = client.delete("/tools/unregister/tool_to_remove")
        
        assert response.status_code == 200
        assert "removed" in response.json()["message"]
        
        # Verify it's gone
        tools = client.get("/tools/").json()
        assert "tool_to_remove" not in tools["tools"]

    def test_unregister_nonexistent_tool_fails(self, client):
        """Verify unregistering non-existent tool returns 404."""
        response = client.delete("/tools/unregister/ghost_tool")
        
        assert response.status_code == 404
        assert "not a dynamically registered" in response.json()["detail"]

    def test_unregister_builtin_tool_fails(self, client):
        """Verify unregistering built-in tools fails."""
        # "echo" is a built-in tool from Pattern B, not external
        response = client.delete("/tools/unregister/echo")
        
        assert response.status_code == 404


# =============================================================================
# HTTP Method Support Tests
# =============================================================================

class TestHTTPMethodSupport:
    """Tests for different HTTP methods in external tools."""

    def test_register_get_tool(self, client):
        """Verify GET method tools can be registered."""
        config = {
            "name": "get_tool",
            "description": "GET method tool",
            "endpoint_url": "https://jsonplaceholder.typicode.com/posts",
            "http_method": "GET",
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200
        assert response.json()["tool"]["method"] == "GET"

    def test_register_post_tool(self, client):
        """Verify POST method tools can be registered."""
        config = {
            "name": "post_tool",
            "description": "POST method tool",
            "endpoint_url": "https://jsonplaceholder.typicode.com/posts",
            "http_method": "POST",
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200
        assert response.json()["tool"]["method"] == "POST"

    def test_register_put_tool(self, client):
        """Verify PUT method tools can be registered."""
        config = {
            "name": "put_tool",
            "description": "PUT method tool",
            "endpoint_url": "https://jsonplaceholder.typicode.com/posts/1",
            "http_method": "PUT",
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200
        assert response.json()["tool"]["method"] == "PUT"

    def test_register_delete_tool(self, client):
        """Verify DELETE method tools can be registered."""
        config = {
            "name": "delete_tool",
            "description": "DELETE method tool",
            "endpoint_url": "https://jsonplaceholder.typicode.com/posts/1",
            "http_method": "DELETE",
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200
        assert response.json()["tool"]["method"] == "DELETE"


# =============================================================================
# Tool Tags Tests
# =============================================================================

class TestToolTags:
    """Tests for tool tag functionality."""

    def test_register_tool_with_tags(self, client):
        """Verify tools can be registered with tags."""
        config = {
            "name": "tagged_tool",
            "description": "A tool with tags",
            "endpoint_url": "https://api.example.com/data",
            "http_method": "GET",
            "tags": ["category1", "category2", "important"],
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200

    def test_register_tool_without_tags(self, client):
        """Verify tools can be registered without tags."""
        config = {
            "name": "untagged_tool",
            "description": "A tool without tags",
            "endpoint_url": "https://api.example.com/data",
            "http_method": "GET",
            # No tags field
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200


# =============================================================================
# Integration Tests
# =============================================================================

class TestRuntimeRegistrationIntegration:
    """Integration tests for runtime tool registration."""

    def test_full_lifecycle_register_list_unregister(self, client):
        """Test complete lifecycle: register → list → unregister."""
        # Initial state
        initial = client.get("/tools/").json()
        initial_count = initial["total_tools"]
        
        # Register 3 tools
        for i in range(3):
            config = {
                "name": f"lifecycle_tool_{i}",
                "description": f"Lifecycle test tool {i}",
                "endpoint_url": f"https://api.example.com/{i}",
                "http_method": "GET",
            }
            response = client.post("/tools/register", json=config)
            assert response.status_code == 200
        
        # Verify all registered
        after_register = client.get("/tools/").json()
        assert after_register["total_tools"] == initial_count + 3
        
        # Unregister all
        for i in range(3):
            response = client.delete(f"/tools/unregister/lifecycle_tool_{i}")
            assert response.status_code == 200
        
        # Verify back to original count
        after_unregister = client.get("/tools/").json()
        assert after_unregister["total_tools"] == initial_count

    def test_rest_api_endpoints_still_work(self, client):
        """Verify REST API endpoints still work alongside tool management."""
        # Tool management
        client.post("/tools/register", json={
            "name": "side_tool",
            "description": "Side tool",
            "endpoint_url": "https://example.com",
            "http_method": "GET",
        })
        
        # REST API should still work
        response = client.get("/items")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Health check should still work
        response = client.get("/health")
        assert response.status_code == 200


# =============================================================================
# POST Method with Payload Tests
# =============================================================================

class TestPOSTMethodWithPayload:
    """Tests for POST method tools with request payloads."""

    def test_register_post_tool_with_json_payload(self, client):
        """Verify POST tool can be registered with JSON body support."""
        config = {
            "name": "create_post_tool",
            "description": "Create a new post with title and body",
            "endpoint_url": "https://jsonplaceholder.typicode.com/posts",
            "http_method": "POST",
            "tags": ["create", "post"],
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["tool"]["method"] == "POST"
        assert data["tool"]["name"] == "create_post_tool"

    def test_register_post_tool_with_complex_payload_schema(self, client):
        """Verify POST tool registration for complex nested payload."""
        config = {
            "name": "create_user_tool",
            "description": "Create a new user with nested address and company",
            "endpoint_url": "https://jsonplaceholder.typicode.com/users",
            "http_method": "POST",
            "tags": ["create", "user", "complex"],
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "create_user_tool" in data["message"]

    def test_register_put_tool_with_update_payload(self, client):
        """Verify PUT tool can be registered for update operations."""
        config = {
            "name": "update_post_tool",
            "description": "Update an existing post with new title and body",
            "endpoint_url": "https://jsonplaceholder.typicode.com/posts/1",
            "http_method": "PUT",
            "tags": ["update", "post"],
        }
        
        response = client.post("/tools/register", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["tool"]["method"] == "PUT"

    def test_multiple_post_tools_with_different_payloads(self, client):
        """Verify multiple POST tools can be registered with different payload types."""
        tools = [
            {
                "name": "create_comment",
                "description": "Create a comment with postId, name, email, and body",
                "endpoint_url": "https://jsonplaceholder.typicode.com/comments",
                "http_method": "POST",
                "tags": ["create", "comment"],
            },
            {
                "name": "create_album",
                "description": "Create an album with userId and title",
                "endpoint_url": "https://jsonplaceholder.typicode.com/albums",
                "http_method": "POST",
                "tags": ["create", "album"],
            },
            {
                "name": "create_todo",
                "description": "Create a todo with userId, title, and completed status",
                "endpoint_url": "https://jsonplaceholder.typicode.com/todos",
                "http_method": "POST",
                "tags": ["create", "todo"],
            },
        ]
        
        for tool_config in tools:
            response = client.post("/tools/register", json=tool_config)
            assert response.status_code == 200
            assert response.json()["tool"]["method"] == "POST"
        
        # Verify all tools are registered
        tools_response = client.get("/tools/")
        tools_data = tools_response.json()
        
        for tool_config in tools:
            assert tool_config["name"] in tools_data["tools"]
            assert tool_config["name"] in tools_data["external_tools"]

    def test_post_tool_lifecycle_with_payload(self, client):
        """Test complete lifecycle of POST tool: register → verify → unregister."""
        initial = client.get("/tools/").json()
        initial_count = initial["total_tools"]
        
        # Register POST tool
        config = {
            "name": "lifecycle_post_tool",
            "description": "POST tool for lifecycle test with JSON payload",
            "endpoint_url": "https://jsonplaceholder.typicode.com/posts",
            "http_method": "POST",
            "tags": ["lifecycle", "test"],
        }
        
        register_response = client.post("/tools/register", json=config)
        assert register_response.status_code == 200
        
        # Verify registered
        tools = client.get("/tools/").json()
        assert tools["total_tools"] == initial_count + 1
        assert "lifecycle_post_tool" in tools["external_tools"]
        
        # Unregister
        unregister_response = client.delete("/tools/unregister/lifecycle_post_tool")
        assert unregister_response.status_code == 200
        
        # Verify removed
        final_tools = client.get("/tools/").json()
        assert final_tools["total_tools"] == initial_count
        assert "lifecycle_post_tool" not in final_tools["external_tools"]


# =============================================================================
# Mixed HTTP Methods Integration Tests
# =============================================================================

class TestMixedHTTPMethodsIntegration:
    """Integration tests for mixing GET, POST, PUT, DELETE tools."""

    def test_register_crud_tools_for_resource(self, client):
        """Verify full CRUD set of tools can be registered for a resource."""
        base_url = "https://jsonplaceholder.typicode.com/posts"
        
        crud_tools = [
            {
                "name": "posts_list",
                "description": "List all posts",
                "endpoint_url": base_url,
                "http_method": "GET",
                "tags": ["posts", "read"],
            },
            {
                "name": "posts_create",
                "description": "Create a new post with title, body, and userId",
                "endpoint_url": base_url,
                "http_method": "POST",
                "tags": ["posts", "create"],
            },
            {
                "name": "posts_update",
                "description": "Update post with id=1 with new title and body",
                "endpoint_url": f"{base_url}/1",
                "http_method": "PUT",
                "tags": ["posts", "update"],
            },
            {
                "name": "posts_delete",
                "description": "Delete post with id=1",
                "endpoint_url": f"{base_url}/1",
                "http_method": "DELETE",
                "tags": ["posts", "delete"],
            },
        ]
        
        # Register all CRUD tools
        for tool_config in crud_tools:
            response = client.post("/tools/register", json=tool_config)
            assert response.status_code == 200
        
        # Verify all registered
        tools = client.get("/tools/").json()
        for tool_config in crud_tools:
            assert tool_config["name"] in tools["tools"]
        
        # Verify methods are correct
        assert "posts_list" in tools["external_tools"]
        assert "posts_create" in tools["external_tools"]
        assert "posts_update" in tools["external_tools"]
        assert "posts_delete" in tools["external_tools"]

    def test_unregister_only_post_tools(self, client):
        """Verify only POST tools can be selectively unregistered."""
        # Register mix of GET and POST tools
        tools = [
            {"name": "get_data", "description": "Get data", "endpoint_url": "https://example.com/data", "http_method": "GET"},
            {"name": "post_data", "description": "Post data", "endpoint_url": "https://example.com/data", "http_method": "POST"},
            {"name": "get_users", "description": "Get users", "endpoint_url": "https://example.com/users", "http_method": "GET"},
            {"name": "post_users", "description": "Post users", "endpoint_url": "https://example.com/users", "http_method": "POST"},
        ]
        
        for tool in tools:
            client.post("/tools/register", json=tool)
        
        # Unregister only POST tools
        client.delete("/tools/unregister/post_data")
        client.delete("/tools/unregister/post_users")
        
        # Verify GET tools still exist
        remaining = client.get("/tools/").json()
        assert "get_data" in remaining["external_tools"]
        assert "get_users" in remaining["external_tools"]
        assert "post_data" not in remaining["external_tools"]
        assert "post_users" not in remaining["external_tools"]
