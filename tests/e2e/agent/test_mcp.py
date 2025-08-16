import pytest
from fastmcp import Client, FastMCP
from pytest_mock import MockerFixture

from askui.agent import VisionAgent
from askui.models.shared.tools import ToolCollection


@pytest.mark.asyncio
async def test_mcp(mocker: MockerFixture) -> None:  # noqa: F821
    mcp = FastMCP("Vision Agent MCP App")

    test_tool_mock = mocker.Mock(return_value=None)

    @mcp.tool
    def test_tool() -> None:
        return test_tool_mock()

    mcp_client = Client(mcp)
    async with mcp_client:
        with VisionAgent() as agent:
            agent.act(
                "Call the test tool",
                tools=ToolCollection(
                    mcp_client=mcp_client,
                ),
            )

    test_tool_mock.assert_called_once()


def test_mcp(mocker: MockerFixture) -> None:  # noqa: F821
    mcp = FastMCP("Vision Agent MCP App")

    test_tool_mock = mocker.Mock(return_value=None)

    @mcp.tool
    def test_tool() -> None:
        return test_tool_mock()

    mcp_client = Client(mcp)
    async with mcp_client:
        with VisionAgent() as agent:
            agent.act(
                "Call the test tool",
                tools=ToolCollection(
                    mcp_client=mcp_client,
                ),
            )

    test_tool_mock.assert_called_once()
