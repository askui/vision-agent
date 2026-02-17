from fastmcp import FastMCP

from askui.tools.playwright.agent_os import PlaywrightAgentOs
from askui.tools.playwright.tools import (
    PlaywrightBackTool,
    PlaywrightForwardTool,
    PlaywrightGetPageTitleTool,
    PlaywrightGetPageUrlTool,
    PlaywrightGotoTool,
)

mcp = FastMCP(name="AskUI Web MCP")

# Use a shared Agent OS instance for the MCP server
WEB_AGENT_OS = PlaywrightAgentOs(headless=True)

TOOLS = [
    PlaywrightGotoTool(WEB_AGENT_OS),
    PlaywrightBackTool(WEB_AGENT_OS),
    PlaywrightForwardTool(WEB_AGENT_OS),
    PlaywrightGetPageTitleTool(WEB_AGENT_OS),
    PlaywrightGetPageUrlTool(WEB_AGENT_OS),
]

for tool in TOOLS:
    mcp.add_tool(tool.to_mcp_tool({"web"}))
