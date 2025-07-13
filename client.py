import asyncio
import os
import json


from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing import Any, Dict, List

load_dotenv("./.env")

global session

async def main():
    test_value = os.getenv("TEST")
    print(f"Value from .env: {test_value}")

    # Connect to the MCP Server
    async with streamablehttp_client("http://localhost:8000/mcp") as (
        read_stream,
        write_stream,
        get_session_id,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            # initialise the session
            await session.initialize()

            tools_result = await session.list_tools()
            print("Available tools:")
            for tool in tools_result.tools:
                print(f"- {tool.name}: {tool.description}")

            async def get_mcp_tools() -> List[Dict[str, Any]]:
                """Get a list of available MCP tools in OpenAI format.
                Returns:
                    A list of tools in OpenAI format."""
                
                tools_result = await session.list_tools()
                return [{
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    }
                } for tool in tools_result.tools
                ]



            
            # Call the sum tool
            sum_result = await session.call_tool("sum", arguments= {"a": 5, "b": 3})
            print(f"Sum result: {sum_result.content[0].text}")

            # Call the say_hello tool
            hello_result = await session.call_tool("say_hello", arguments={"name": "Nick"})
            print(f"Greeting: {hello_result.content[0].text}")

            # Call the get_platforms_info() tool
            platforms_result = await session.call_tool("get_platforms_info")
            print(f"Platforms information: {platforms_result.content[0].text}")

            #openAI tools
            open_ai_tools = await get_mcp_tools()
            print("OpenAI formatted tools:")
            for tool in open_ai_tools:
                print(f"- {tool['function']['name']}: {tool['function']['description']}")
            
            openai_client = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # Example query to the OpenAI model

            query = "Example query"
            
            response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query}],
            tools=open_ai_tools,
            tool_choice="auto")

            # Get assistant's response
            assistant_message = response.choices[0].message
            print(f"Assistant's response: {assistant_message.content}")

            # Initialize conversation with user query and assistant response
            messages = [
            {"role": "user", "content": query},
            assistant_message
        ]

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
                
                # Get final response from OpenAI with tool results
                final_response = await openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=open_ai_tools,
                    tool_choice="none",  # Don't allow more tool calls
            )

            print(final_response.choices[0].message.content)

            
if __name__ == "__main__":
    asyncio.run(main())  # Run the main function in the event loop