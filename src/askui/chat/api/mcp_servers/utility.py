import asyncio
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP(name="AskUI Utility MCP")


@mcp.tool(
    description="Wait for a specified number of seconds",
    tags={"utility"},
)
async def utility_wait(
    seconds: Annotated[
        float,
        Field(ge=0.0, le=3600.0, description="Number of seconds to wait (0-3600)"),
    ],
) -> str:
    """
    Wait for the specified number of seconds.

    Args:
        seconds (float): Number of seconds to wait, between 0 and 3600 (1 hour).

    Returns:
        str: Confirmation message indicating the wait is complete.

    Example:
        ```python
        wait(5.0)  # Wait for 5 seconds
        ```
    """
    if seconds == 0:
        return "Wait completed immediately (0 seconds)"

    await asyncio.sleep(seconds)
    return f"Wait completed after {seconds} seconds"
