import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    

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
            
            # Call the sum tool
            sum_result = await session.call_tool("sum", arguments= {"a": 5, "b": 3})
            print(f"Sum result: {sum_result.content[0].text}")

            # Call the say_hello tool
            hello_result = await session.call_tool("say_hello", arguments={"name": "Nick"})
            print(f"Greeting: {hello_result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())  # Run the main function in the event loop