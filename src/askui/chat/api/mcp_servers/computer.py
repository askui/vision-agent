from fastmcp import FastMCP

from askui.tools.askui.askui_controller import AskUiControllerClient
from askui.tools.computer import (
    ComputerDisconnectTool,
    ComputerGetMousePositionTool,
    ComputerKeyboardPressedTool,
    ComputerKeyboardReleaseTool,
    ComputerKeyboardTapTool,
    ComputerListDisplaysTool,
    ComputerMouseClickTool,
    ComputerMouseHoldDownTool,
    ComputerMouseReleaseTool,
    ComputerMouseScrollTool,
    ComputerMoveMouseTool,
    ComputerReconnectTool,
    ComputerRetrieveActiveDisplayTool,
    ComputerScreenshotTool,
    ComputerSetActiveDisplayTool,
    ComputerTypeTool,
)
from askui.tools.computer_agent_os_facade import ComputerAgentOsFacade

mcp = FastMCP(name="AskUI Computer MCP")

COMPUTER_AGENT_OS = AskUiControllerClient()
COMPUTER_AGENT_OS_FACADE = ComputerAgentOsFacade(COMPUTER_AGENT_OS)

TOOLS = [
    ComputerGetMousePositionTool(COMPUTER_AGENT_OS_FACADE),
    ComputerKeyboardPressedTool(COMPUTER_AGENT_OS_FACADE),
    ComputerKeyboardReleaseTool(COMPUTER_AGENT_OS_FACADE),
    ComputerKeyboardTapTool(COMPUTER_AGENT_OS_FACADE),
    ComputerListDisplaysTool(COMPUTER_AGENT_OS_FACADE),
    ComputerMouseClickTool(COMPUTER_AGENT_OS_FACADE),
    ComputerMouseHoldDownTool(COMPUTER_AGENT_OS_FACADE),
    ComputerMouseReleaseTool(COMPUTER_AGENT_OS_FACADE),
    ComputerMouseScrollTool(COMPUTER_AGENT_OS_FACADE),
    ComputerMoveMouseTool(COMPUTER_AGENT_OS_FACADE),
    ComputerRetrieveActiveDisplayTool(COMPUTER_AGENT_OS_FACADE),
    ComputerScreenshotTool(COMPUTER_AGENT_OS_FACADE),
    ComputerSetActiveDisplayTool(COMPUTER_AGENT_OS_FACADE),
    ComputerTypeTool(COMPUTER_AGENT_OS_FACADE),
    ComputerReconnectTool(COMPUTER_AGENT_OS_FACADE),
    ComputerDisconnectTool(COMPUTER_AGENT_OS_FACADE),
]

for tool in TOOLS:
    mcp.add_tool(tool.to_mcp_tool({"computer"}))
