# server.py
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo", stateless_http=True)


# Add an addition tool
@mcp.tool()
def sum(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b 

@mcp.tool()
def say_hello(name: str) -> str:
    """Return a greeting message"""
    return f"Hello, {name}!"


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

mcp.run(transport="streamable-http")  # Start the MCP server


