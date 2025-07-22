from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools.tool import Tool

from askui.agent import VisionAgent


@dataclass
class AppContext:
    vision_agent: VisionAgent


@asynccontextmanager
async def mcp_lifespan(server: FastMCP[Any]) -> AsyncIterator[AppContext]:  # noqa: ARG001
    with VisionAgent(display=2) as vision_agent:
        server.add_tool(Tool.from_function(vision_agent.click))
        yield AppContext(vision_agent=vision_agent)


mcp = FastMCP("Vision Agent MCP App", lifespan=mcp_lifespan)
