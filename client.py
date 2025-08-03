"""
client.py

Handles communication with MCP server, including sending queries and receiving responses.
"""

import asyncio
import os
import json


from contextlib import asynccontextmanager
from typing import Any, Dict, List, AsyncGenerator

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion


load_dotenv("./.env")


@asynccontextmanager
async def create_mcp_session(server_path: str) -> AsyncGenerator[ClientSession, None]:
    """Create an asynchronous context manager for an MCP client session.
    Args:
        server_path (str): The URL path to the MCP server.
    Yields:
        ClientSession: An active MCP client session."""
    async with streamablehttp_client(server_path) as (
        read_stream,
        write_stream,
        _get_session_id,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


async def get_mcp_tools(session: ClientSession) -> List[Dict[str, Any]]:
    """Get a list of available MCP tools in OpenAI format.
    Args:
        session (ClientSession): The active MCP client session.
    Returns:
        A list of tools in OpenAI format.
    """
    tools_result = await session.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in tools_result.tools
    ]


async def handle_query(
    session: ClientSession, query: str, openai_client: AsyncOpenAI, openai_model: str
) -> ChatCompletion:
    """Handle a user query by calling the appropriate MCP tools and return a response
    Args:
        session (ClientSession): The active MCP client session.
        query (str): The user query to process.
        openai_client (AsyncOpenAI): The OpenAI client to use for generating responses.
    Returns:
        ChatCompletion: The final response from OpenAI after processing the query and tool calls.
    """
    final_response = None
    
    print("fetching tools from MCP server...")
    open_ai_tools = await get_mcp_tools(session)

    print("Tools fetched successfully...")
    print("Sending query to OpenAI along with available MCP tools...")
    # Initialize OpenAI client
    response = await openai_client.chat.completions.create(
        model=openai_model,
        messages=[{"role": "user", "content": query}],
        tools=open_ai_tools,
        tool_choice="auto",
    )

    print("Open AI response received, with tools requested if any...")
    # Get assistant's response
    assistant_message = response.choices[0].message

    # Initialize conversation with user query and assistant response
    messages = [{"role": "user", "content": query}, assistant_message]

    print("Calling the MCP server for tools requested by OpenAI...")
    # Handle tool calls if present
    if assistant_message.tool_calls:
        # Process each tool call
        for tool_call in assistant_message.tool_calls:
            # Execute tool call
            result = await session.call_tool(
                tool_call.function.name,
                arguments=json.loads(tool_call.function.arguments),
            )
            # Add tool response to conversation
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result.content[0].text,
                }
            )

        print("Passing tool results back to OpenAI...")
        # Get final response from OpenAI with tool results

        final_response = await openai_client.chat.completions.create(
            model=openai_model,
            messages=messages,
            tools=open_ai_tools,
            tool_choice="none",  # Don't allow more tool calls
        )
    print("Final response received from OpenAI after processing tool results...\n \n")

    if (final_response):
        return final_response.choices[0].message.content
    
    print("No content in final response, returning assistant message instead... \n \n")
    return assistant_message.content


async def main():
    """Main function to run the MCP client."""
    try:
        server_path = "http://localhost:8000/mcp"
        openai_model = "gpt-4o-mini"

        query = input("Enter query to send: ")

        async with create_mcp_session(server_path) as session:
            # You can now use the session to interact with the MCP server
            print("Connected to MCP server successfully...")

            # Initialize OpenAI client with API key from environment variable
            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            #query = """I need to host a web application for my new digital service. What platform
            #can I use to host this web application?"""

            result = await handle_query(session, query, openai_client, openai_model)

            print(result)

    except Exception as e:
        print(f"Error connecting to MCP server, check that the server is running: {e}")


if __name__ == "__main__":
    asyncio.run(main())  # Run the main function in the event loop
