from fastmcp import FastMCP
from fastmcp.tools import Tool

from askui.chat.api.dependencies import get_settings
from askui.tools.testing.execution_tools import (
    CreateExecutionTool,
    DeleteExecutionTool,
    ListExecutionTool,
    ModifyExecutionTool,
    RetrieveExecutionTool,
)
from askui.tools.testing.feature_tools import (
    CreateFeatureTool,
    DeleteFeatureTool,
    ListFeatureTool,
    ModifyFeatureTool,
    RetrieveFeatureTool,
)
from askui.tools.testing.scenario_tools import (
    CreateScenarioTool,
    DeleteScenarioTool,
    ListScenarioTool,
    ModifyScenarioTool,
    RetrieveScenarioTool,
)

mcp = FastMCP(name="AskUI Testing MCP")

settings = get_settings()
base_dir = settings.data_dir / "testing"

FEATURE_TOOLS = [
    CreateFeatureTool(base_dir),
    RetrieveFeatureTool(base_dir),
    ListFeatureTool(base_dir),
    ModifyFeatureTool(base_dir),
    DeleteFeatureTool(base_dir),
]

SCENARIO_TOOLS = [
    CreateScenarioTool(base_dir),
    RetrieveScenarioTool(base_dir),
    ListScenarioTool(base_dir),
    ModifyScenarioTool(base_dir),
    DeleteScenarioTool(base_dir),
]

EXECUTION_TOOLS = [
    CreateExecutionTool(base_dir),
    RetrieveExecutionTool(base_dir),
    ListExecutionTool(base_dir),
    ModifyExecutionTool(base_dir),
    DeleteExecutionTool(base_dir),
]


TOOLS = [
    *FEATURE_TOOLS,
    *SCENARIO_TOOLS,
    *EXECUTION_TOOLS,
]


for tool in TOOLS:
    tags = {"testing"}
    if tool in FEATURE_TOOLS:
        tags.add("feature")
    if tool in SCENARIO_TOOLS:
        tags.add("scenario")
    if tool in EXECUTION_TOOLS:
        tags.add("execution")
    mcp.add_tool(
        Tool.from_function(
            tool.__call__,
            name=tool.name,
            description=tool.description,
            tags=tags,
        ),
    )
