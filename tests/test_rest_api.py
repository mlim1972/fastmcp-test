"""
Tests for REST API Endpoints

This module tests the FastAPI REST API endpoints directly,
independent of the MCP conversion layer.

Run tests with:
    uv run pytest tests/test_rest_api.py -v
"""

import pytest
from fastapi.testclient import TestClient

from dynamic_mcp.api.routes import app, _items_db


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    """Reset the in-memory database before each test."""
    from dynamic_mcp.api.routes import _items_db, ItemResponse
    
    # Store original state
    original_items = dict(_items_db)
    
    yield
    
    # Restore original state after test
    _items_db.clear()
    _items_db.update(original_items)


# =============================================================================
# Health Check Tests
# =============================================================================

class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check_returns_ok(self, client):
        """Verify health check returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "dynamic-mcp-tools"


# =============================================================================
# Item CRUD Tests
# =============================================================================

class TestItemCRUD:
    """Tests for Item CRUD operations."""

    def test_list_items_returns_all_items(self, client):
        """Verify list_items returns all items."""
        response = client.get("/items")
        
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        assert len(items) >= 3  # Initial seed data

    def test_get_item_returns_specific_item(self, client):
        """Verify get_item returns the requested item."""
        response = client.get("/items/1")
        
        assert response.status_code == 200
        item = response.json()
        assert item["id"] == 1
        assert item["name"] == "Laptop"

    def test_get_item_not_found(self, client):
        """Verify get_item returns 404 for non-existent item."""
        response = client.get("/items/9999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_item(self, client):
        """Verify create_item creates a new item."""
        new_item = {
            "name": "Test Item",
            "description": "A test item",
            "price": 49.99,
        }
        
        response = client.post("/items", json=new_item)
        
        assert response.status_code == 200
        item = response.json()
        assert item["name"] == "Test Item"
        assert item["price"] == 49.99
        assert "id" in item

    def test_create_item_without_description(self, client):
        """Verify create_item works without optional description."""
        new_item = {
            "name": "Simple Item",
            "price": 19.99,
        }
        
        response = client.post("/items", json=new_item)
        
        assert response.status_code == 200
        item = response.json()
        assert item["name"] == "Simple Item"
        assert item["description"] is None

    def test_create_item_validation_error(self, client):
        """Verify create_item rejects invalid data."""
        invalid_item = {
            "name": "Bad Item",
            "price": -10,  # Negative price should fail
        }
        
        response = client.post("/items", json=invalid_item)
        
        assert response.status_code == 422  # Validation error

    def test_update_item(self, client):
        """Verify update_item modifies an existing item."""
        updated_data = {
            "name": "Updated Laptop",
            "price": 1299.99,
        }
        
        response = client.put("/items/1", json=updated_data)
        
        assert response.status_code == 200
        item = response.json()
        assert item["name"] == "Updated Laptop"
        assert item["price"] == 1299.99

    def test_update_item_not_found(self, client):
        """Verify update_item returns 404 for non-existent item."""
        response = client.put("/items/9999", json={"name": "Ghost", "price": 1.0})
        
        assert response.status_code == 404

    def test_delete_item(self, client):
        """Verify delete_item removes an item."""
        # First verify item exists
        response = client.get("/items/1")
        assert response.status_code == 200
        
        # Delete the item
        response = client.delete("/items/1")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()
        
        # Verify it's gone
        response = client.get("/items/1")
        assert response.status_code == 404

    def test_delete_item_not_found(self, client):
        """Verify delete_item returns 404 for non-existent item."""
        response = client.delete("/items/9999")
        
        assert response.status_code == 404


# =============================================================================
# Calculate Endpoint Tests
# =============================================================================

class TestCalculate:
    """Tests for calculation endpoint."""

    def test_calculate_add(self, client):
        """Verify addition operation."""
        response = client.post("/calculate", json={
            "operation": "add",
            "a": 10,
            "b": 5,
        })
        
        assert response.status_code == 200
        result = response.json()
        assert result["result"] == 15

    def test_calculate_subtract(self, client):
        """Verify subtraction operation."""
        response = client.post("/calculate", json={
            "operation": "subtract",
            "a": 10,
            "b": 3,
        })
        
        assert response.status_code == 200
        result = response.json()
        assert result["result"] == 7

    def test_calculate_multiply(self, client):
        """Verify multiplication operation."""
        response = client.post("/calculate", json={
            "operation": "multiply",
            "a": 6,
            "b": 7,
        })
        
        assert response.status_code == 200
        result = response.json()
        assert result["result"] == 42

    def test_calculate_divide(self, client):
        """Verify division operation."""
        response = client.post("/calculate", json={
            "operation": "divide",
            "a": 20,
            "b": 4,
        })
        
        assert response.status_code == 200
        result = response.json()
        assert result["result"] == 5.0

    def test_calculate_divide_by_zero(self, client):
        """Verify division by zero returns error."""
        response = client.post("/calculate", json={
            "operation": "divide",
            "a": 10,
            "b": 0,
        })
        
        assert response.status_code == 400
        assert "zero" in response.json()["detail"].lower()

    def test_calculate_invalid_operation(self, client):
        """Verify invalid operation returns validation error."""
        response = client.post("/calculate", json={
            "operation": "power",  # Not a valid operation
            "a": 2,
            "b": 3,
        })
        
        assert response.status_code == 422  # Validation error
