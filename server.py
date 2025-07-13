# server.py
from mcp.server.fastmcp import FastMCP

import os
import json

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

# Tool for getting the available platforms
@mcp.tool()
def get_platforms_info() -> str:
    """Retrieves the entire platforms database as a formatted string.

    Returns:
        A formatted string containing all platform information.
    """
    try:
        db_path = os.path.join(os.path.dirname(__file__), "data", "db.json")

        with open(db_path, "r") as db_file:
            db = json.load(db_file)
        
        # Format the database content as a string
        formatted_string = "Here is the retrieved database content:\n\n"

        if isinstance(db, list):
            for i, item in enumerate(db, 1):
                if isinstance(item, dict):
                    formatted_string += f"Item {i}:\n"
                    for key, value in item.items():
                        formatted_string += f"  {key}: {value}\n"
        else:
            return "Database content is not in the expected format."

        return formatted_string
    
    except FileNotFoundError:
        return "Database file not found."
    except json.JSONDecodeError:
        return "Error decoding the database file."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
    



mcp.run(transport="streamable-http")  # Start the MCP server


