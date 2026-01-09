# MCP

## Table of Contents

- [What is MCP?](#what-is-mcp)
- [Our MCP Support](#our-mcp-support)
- [How to Use MCP with AskUI](#how-to-use-mcp-with-askui)

## What is MCP?

The Model Context Protocol (MCP) is a standardized way to provide context and tools to Large Language Models (LLMs). It acts as a universal interface - often described as "the USB-C port for AI" - that allows LLMs to connect to external resources and functionality in a secure, standardized manner.

MCP servers can:
- **Expose data** through `Resources` (similar to GET endpoints for loading information into the LLM's context)
- **Provide functionality** through `Tools` (similar to POST endpoints for executing code or producing side effects)
- **Define interaction patterns** through `Prompts` (reusable templates for LLM interactions)

For more information, see the [MCP specification](https://modelcontextprotocol.io/docs/getting-started/intro).

## Our MCP Support

We support the use of tools from MCP servers through the library `AgentBase.act()` (and extending classes, e.g., `VisionAgent.act()`, `AndroidVisionAgent.act()`).

The use of tools is comprised of listing the tools available, passing them on to the model and calling them if the model requests them to be called.

The library uses [`fastmcp`](https://gofastmcp.com/getting-started/welcome) for MCP integration.

## How to Use MCP with AskUI

You can integrate MCP tools directly into your AskUI agents by creating an MCP client and passing it to the `ToolCollection`:

```python
from fastmcp import Client
from fastmcp.mcp_config import MCPConfig, RemoteMCPServer

from askui.agent import VisionAgent
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.models.shared.tools import ToolCollection
from askui.tools.mcp.config import StdioMCPServer

# Create MCP configuration
mcp_config = MCPConfig(
    mcpServers={
        # Make sure to use our patch of StdioMCPServer as we don't support the official one
        "test_stdio_server": StdioMCPServer(
            command="python", args=["-m", "askui.tools.mcp.servers.stdio"]
        ),
        "test_sse_server": RemoteMCPServer(url="http://127.0.0.1:8001/sse/"),
    }
)

# Create MCP client
mcp_client = Client(mcp_config)

# Create tool collection with MCP tools
tools = ToolCollection(mcp_client=mcp_client)


def on_message(param: OnMessageCbParam) -> MessageParam | None:
    print(param.message.model_dump_json())
    return param.message


# Use with VisionAgent
with VisionAgent() as agent:
    agent.act(
        "Use the `test_stdio_server_test_stdio_tool`",
        tools=tools,
        on_message=on_message,
    )
```

Tools are appended to the default tools of the agent, potentially, overriding them.

For different ways to construct `Client`s see the [fastmcp documentation](https://gofastmcp.com/clients/client).

Notice that the tool name (`test_stdio_tool`) is prefixed with the server name (`test_stdio_server`) to avoid conflicts.


If you would like to try out the `test_sse_server` you can run the following command before executing the code above:

```bash
python -m askui.tools.mcp.servers.sse
```

**Caveats and Limitations**

- **No Tool Selection/Filtering**: All MCP tools from connected servers are automatically available
- **Synchronous Code Requirement**: MCP tools must be run from within synchronous code contexts (no `async` or `await` allowed)
- **Limited Tool Response Content Types**: Only text and images (JPEG, PNG, GIF, WebP) are supported
- **Complexity Limits**: Tools are limited in number and complexity by the model's context window

## How to Define Your Own MCP Server

### Different Frameworks

You can build MCP servers using various frameworks and languages:

#### FastMCP (Python) - Recommended

FastMCP provides the most Pythonic and straightforward way to build MCP servers:

```python
from fastmcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool
def my_tool(param: str) -> str:
    """My custom tool description."""
    return f"Processed: {param}"

if __name__ == "__main__":
    mcp.run(transport="stdio")  # For AskUI integration
    # or
    mcp.run(transport="sse", port=8001)  # For remote access
```

#### Official MCP SDKs

The official MCP specification provides SDKs for multiple languages:
[https://modelcontextprotocol.io/docs/sdk](https://modelcontextprotocol.io/docs/sdk)
