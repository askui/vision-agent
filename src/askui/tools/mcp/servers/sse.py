from fastmcp import FastMCP

mcp = FastMCP("Test StdIO MCP App", port=8001)


@mcp.tool
def test_sse_tool() -> str:
    print("test_sse_tool called")
    return "I am a test sse tool"


if __name__ == "__main__":
    mcp.run(transport="sse")
