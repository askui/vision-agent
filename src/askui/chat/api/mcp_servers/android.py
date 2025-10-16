from fastmcp import FastMCP

from askui.chat.api.mcp_servers.android_setup_doc import ANDROID_SETUP_GUIDE
from askui.tools.android.agent_os_facade import AndroidAgentOsFacade
from askui.tools.android.ppadb_agent_os import PpadbAgentOs
from askui.tools.android.tools import (
    AndroidConnectTool,
    AndroidDragAndDropTool,
    AndroidGetConnectedDevicesSerialNumbersTool,
    AndroidGetConnectedDisplaysInfosTool,
    AndroidGetCurrentConnectedDeviceInfosTool,
    AndroidKeyCombinationTool,
    AndroidKeyTapEventTool,
    AndroidScreenshotTool,
    AndroidSelectDeviceBySerialNumberTool,
    AndroidSelectDisplayByIndex,
    AndroidShellTool,
    AndroidSwipeTool,
    AndroidTapTool,
    AndroidTypeTool,
)

mcp = FastMCP(name="AskUI Android MCP")

# Initialize the AndroidAgentOsFacade
ANDROID_AGENT_OS = PpadbAgentOs()
ANDROID_AGENT_OS_FACADE = AndroidAgentOsFacade(ANDROID_AGENT_OS)
TOOLS = [
    AndroidSelectDeviceBySerialNumberTool(ANDROID_AGENT_OS_FACADE),
    AndroidSelectDisplayByIndex(ANDROID_AGENT_OS_FACADE),
    AndroidGetConnectedDevicesSerialNumbersTool(ANDROID_AGENT_OS_FACADE),
    AndroidGetConnectedDisplaysInfosTool(ANDROID_AGENT_OS_FACADE),
    AndroidGetCurrentConnectedDeviceInfosTool(ANDROID_AGENT_OS_FACADE),
    AndroidConnectTool(ANDROID_AGENT_OS_FACADE),
    AndroidScreenshotTool(ANDROID_AGENT_OS_FACADE),
    AndroidTapTool(ANDROID_AGENT_OS_FACADE),
    AndroidTypeTool(ANDROID_AGENT_OS_FACADE),
    AndroidDragAndDropTool(ANDROID_AGENT_OS_FACADE),
    AndroidKeyTapEventTool(ANDROID_AGENT_OS_FACADE),
    AndroidSwipeTool(ANDROID_AGENT_OS_FACADE),
    AndroidKeyCombinationTool(ANDROID_AGENT_OS_FACADE),
    AndroidShellTool(ANDROID_AGENT_OS_FACADE),
]

for tool in TOOLS:
    mcp.add_tool(tool.to_mcp_tool({"android"}))


@mcp.tool(
    description="""Provides step-by-step instructions for setting up Android emulators or real devices.
                Use this tool when no device is connected or the ADB server cannot detect any devices.""",
    tags={"android"},
)
def android_setup_helper() -> str:
    return ANDROID_SETUP_GUIDE
