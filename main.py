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

    instructions = "You are able to manage questions from a client about the same face being in two different images supplied as urls."
    url1 = 'https://upload.wikimedia.org/wikipedia/commons/c/c1/Lionel_Messi_20180626.jpg'
    url2 = 'https://upload.wikimedia.org/wikipedia/commons/8/8c/Cristiano_Ronaldo_2018.jpg'
    request = f"""
    My name is John and I have two urls and I would like to know if the face in the first url is the same as the face in the second url. 
    The first url is {url1} and the second url is: {url2}.
    """
    model = "gpt-4.1-mini"

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(name="face_manager", instructions=instructions, model=model, mcp_servers=[mcp_server])
        # could use a trace
        result = await Runner.run(agent, request)
        print(result.final_output)

if __name__ == "__main__":
    load_dotenv(override=True)
    PRINT_TOOLS = True
    asyncio.run(main())
