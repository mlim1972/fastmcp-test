"""
REST API Routes

This module defines the FastAPI application with REST endpoints for:
- Item CRUD operations (create, read, update, delete)
- A calculation endpoint for arithmetic operations

These endpoints will be automatically converted to MCP tools using
FastMCP.from_fastapi(), demonstrating dynamic tool registration.

The docstrings on each endpoint become the tool descriptions that
MCP clients see, so they should be clear and informative.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal


# =============================================================================
# Pydantic Models
# =============================================================================

class Item(BaseModel):
    """Model for creating/updating an item."""
    name: str = Field(..., description="Name of the item")
    description: str | None = Field(None, description="Optional description of the item")
    price: float = Field(..., gt=0, description="Price of the item (must be positive)")


class ItemResponse(BaseModel):
    """Model for item responses including the ID."""
    id: int = Field(..., description="Unique identifier of the item")
    name: str = Field(..., description="Name of the item")
    description: str | None = Field(None, description="Optional description of the item")
    price: float = Field(..., description="Price of the item")


class CalculationRequest(BaseModel):
    """Model for calculation requests."""
    operation: Literal["add", "subtract", "multiply", "divide"] = Field(
        ..., description="The arithmetic operation to perform"
    )
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")


class CalculationResponse(BaseModel):
    """Model for calculation responses."""
    operation: str = Field(..., description="The operation that was performed")
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    result: float = Field(..., description="Result of the calculation")


# =============================================================================
# In-Memory Database
# =============================================================================

# Simple in-memory storage for items
_items_db: dict[int, ItemResponse] = {
    1: ItemResponse(id=1, name="Laptop", description="A powerful laptop", price=999.99),
    2: ItemResponse(id=2, name="Mouse", description="Wireless mouse", price=29.99),
    3: ItemResponse(id=3, name="Keyboard", description="Mechanical keyboard", price=149.99),
}
_next_id = 4


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Dynamic MCP Tools API",
    description="REST API that will be exposed as MCP tools dynamically",
    version="0.1.0",
)


# =============================================================================
# Item CRUD Endpoints
# These will become MCP tools via FastMCP.from_fastapi()
# =============================================================================

@app.get(
    "/items",
    response_model=list[ItemResponse],
    operation_id="list_items",
    summary="List all items",
)
def list_items() -> list[ItemResponse]:
    """
    List all items in the inventory.
    
    Returns a list of all items currently stored in the system.
    This is useful for getting an overview of available items.
    """
    return list(_items_db.values())


@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    operation_id="get_item",
    summary="Get item by ID",
)
def get_item(item_id: int) -> ItemResponse:
    """
    Get a specific item by its ID.
    
    Args:
        item_id: The unique identifier of the item to retrieve.
        
    Returns:
        The item with the specified ID.
        
    Raises:
        404: If no item with the given ID exists.
    """
    if item_id not in _items_db:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    return _items_db[item_id]


@app.post(
    "/items",
    response_model=ItemResponse,
    operation_id="create_item",
    summary="Create a new item",
)
def create_item(item: Item) -> ItemResponse:
    """
    Create a new item in the inventory.
    
    Args:
        item: The item data including name, optional description, and price.
        
    Returns:
        The created item with its assigned ID.
    """
    global _next_id
    new_item = ItemResponse(id=_next_id, **item.model_dump())
    _items_db[_next_id] = new_item
    _next_id += 1
    return new_item


@app.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    operation_id="update_item",
    summary="Update an existing item",
)
def update_item(item_id: int, item: Item) -> ItemResponse:
    """
    Update an existing item by its ID.
    
    Args:
        item_id: The unique identifier of the item to update.
        item: The new item data.
        
    Returns:
        The updated item.
        
    Raises:
        404: If no item with the given ID exists.
    """
    if item_id not in _items_db:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    updated_item = ItemResponse(id=item_id, **item.model_dump())
    _items_db[item_id] = updated_item
    return updated_item


@app.delete(
    "/items/{item_id}",
    operation_id="delete_item",
    summary="Delete an item",
)
def delete_item(item_id: int) -> dict:
    """
    Delete an item from the inventory.
    
    Args:
        item_id: The unique identifier of the item to delete.
        
    Returns:
        A confirmation message.
        
    Raises:
        404: If no item with the given ID exists.
    """
    if item_id not in _items_db:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    del _items_db[item_id]
    return {"message": f"Item {item_id} deleted successfully"}


# =============================================================================
# Calculation Endpoint
# Demonstrates a computation tool
# =============================================================================

@app.post(
    "/calculate",
    response_model=CalculationResponse,
    operation_id="calculate",
    summary="Perform arithmetic calculation",
)
def calculate(request: CalculationRequest) -> CalculationResponse:
    """
    Perform an arithmetic calculation.
    
    Supports four operations: add, subtract, multiply, divide.
    
    Args:
        request: The calculation request with operation and operands.
        
    Returns:
        The calculation result.
        
    Raises:
        400: If attempting to divide by zero.
    """
    a, b = request.a, request.b
    
    if request.operation == "add":
        result = a + b
    elif request.operation == "subtract":
        result = a - b
    elif request.operation == "multiply":
        result = a * b
    elif request.operation == "divide":
        if b == 0:
            raise HTTPException(status_code=400, detail="Cannot divide by zero")
        result = a / b
    else:
        raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")
    
    return CalculationResponse(
        operation=request.operation,
        a=a,
        b=b,
        result=result,
    )


# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get("/health", operation_id="health_check", summary="Health check")
def health_check() -> dict:
    """
    Check if the API is running.
    
    Returns:
        A status message indicating the API is healthy.
    """
    return {"status": "healthy", "service": "dynamic-mcp-tools"}
