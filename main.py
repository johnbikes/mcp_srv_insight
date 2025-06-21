"""
@Author: John T
@LinkedIn: www.linkedin.com/in/john-tavolacci
@Github: https://github.com/johnbikes/
@Date: 2025-06-07
@Description: Example main for using the MCP server for comparing faces from two URLs using InsightFace.
@License: Apache License 2.0
"""

import asyncio

from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

async def main():
    # just to print the tools
    params = {"command": "uv", "args": ["run", "server.py"]}
    if PRINT_TOOLS:
        async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
            mcp_tools = await server.list_tools()

        print(mcp_tools)

    print("\n" + "-" * 100 + "\n")

    instructions = "You are able to manage questions containing two URLs to determine if they contain the same face according to insightface. If the request contains a single URL, check if it has been seen before."
    url1 = 'https://upload.wikimedia.org/wikipedia/commons/c/c1/Lionel_Messi_20180626.jpg'
    url2 = 'https://upload.wikimedia.org/wikipedia/commons/8/8c/Cristiano_Ronaldo_2018.jpg'
    request = f"""
    My name is John and I have two URLs and would like to determine if they contain the same face according to insightface. 
    The first url is {url1} and the second url is: {url2}.
    """
    model = "gpt-4.1-mini"

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(name="face_manager", instructions=instructions, model=model, mcp_servers=[mcp_server])
        with trace("face_manager"):
            result = await Runner.run(agent, request)
        print(result.final_output)

    print("\n" + "-" * 100 + "\n")

    request = f"""
    My name is John and I have two URLs and would like to determine if they contain the same face according to insightface. 
    The first url is {url1} and the second url is: {url2}.
    I would also like to know more about the inviduals present in each image.
    """

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(name="face_manager", instructions=instructions, model=model, mcp_servers=[mcp_server])
        with trace("face_manager_w_info"):
            result = await Runner.run(agent, request)
        print(result.final_output)

        print("\n" + "-" * 100 + "\n")

        # new Messi url
        url1 = 'https://upload.wikimedia.org/wikipedia/commons/2/26/Leo_messi_barce_2005.jpg'
        request = f"""
        My name is John and I have a single URL and would like to determine if the contained face has been seen before according to insightface. 
        The url is {url1}. If seen, I would like to know the URL of the similar faces.
        """

        with trace("face_manager_has_seen"):
            result = await Runner.run(agent, request)
        print(result.final_output)

        print("\n" + "-" * 100 + "\n")

        # Neymar url
        url1 = 'https://live.staticflickr.com/8778/17145642931_56ea3a6113_b.jpg'
        request = f"""
        My name is John and I have a single URL and would like to determine if the contained face has been seen before according to insightface. 
        The url is {url1}. If seen, I would like to know the URL of the similar faces.
        """

        with trace("face_manager_has_seen_neymar"):
            result = await Runner.run(agent, request)
        print(result.final_output)

if __name__ == "__main__":
    load_dotenv(override=True)
    PRINT_TOOLS = True
    asyncio.run(main())
