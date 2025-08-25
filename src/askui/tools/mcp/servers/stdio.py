from typing import Any

from fastmcp import FastMCP

mcp: FastMCP[Any] = FastMCP("Test StdIO MCP App")


@mcp.tool
def test_stdio_tool() -> str:
    print("test_stdio_tool called")
    return "I am a test stdio tool"


@mcp.tool
def list_values() -> list[str]:
    return ["Optimism", "Creativity", "Intelligence"]


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
