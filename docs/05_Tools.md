# Tools

Tools extend the capabilities of your agents, allowing them to interact with the operating system, perform complex operations, and integrate with external services. This guide covers three main approaches to working with tools in AskUI Vision Agent.

## Table of Contents

- [Part 1: Direct Tool Use](#part-1-direct-tool-use)
  - [Introduction to Agent Tools](#introduction-to-agent-tools)
  - [Agent OS Operations](#agent-os-operations)
  - [Web Browser Control](#web-browser-control)
  - [Clipboard Management](#clipboard-management)
  - [Multi-Monitor Support](#multi-monitor-support)
  - [When to Use Direct Tools vs Agentic Commands](#when-to-use-direct-tools-vs-agentic-commands)
- [Part 2: Extending with MCP](#part-2-extending-with-mcp)
  - [What is MCP?](#what-is-mcp)
  - [MCP Concepts](#mcp-concepts)
  - [Using MCP with AskUI Vision Agent](#using-mcp-with-askui-vision-agent)
    - [With the Library](#with-the-library)
    - [With Chat API](#with-chat-api)
  - [Creating Custom MCP Servers](#creating-custom-mcp-servers)
  - [MCP Limitations and Best Practices](#mcp-limitations-and-best-practices)
- [Part 3: Tool Store](#part-3-tool-store)
  - [Overview](#overview)
  - [How to Use Pre-Built Tools](#how-to-use-pre-built-tools)
  - [Tool Categories](#tool-categories)
- [See Also](#see-also)

---

## Part 1: Direct Tool Use

### Introduction to Agent Tools

Under the hood, agents use a set of tools to interact with your system. While the `act()`, `click()`, and `get()` methods provide high-level abstractions, you can directly access these tools for more precise control over agent behavior.

Direct tool use is ideal when you:
- Need low-level control over specific operations
- Want to combine multiple atomic operations in sequence
- Are building custom automation workflows
- Need to bypass AI model inference for performance

### Agent OS Operations

The Agent OS (Operating System controller) provides direct access to mouse, keyboard, and screen operations:

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    # Mouse clicking
    agent.tools.os.click("left", 2)  # Double-click
    agent.tools.os.click("right", 1)  # Right-click

    # Mouse movement
    agent.tools.os.mouse_move(100, 100)  # Move to absolute coordinates

    # Keyboard operations
    agent.tools.os.keyboard_tap("v", modifier_keys=["control"])  # Paste (Ctrl+V)
    agent.tools.os.keyboard_tap("c", modifier_keys=["control"])  # Copy (Ctrl+C)
    agent.tools.os.keyboard_tap("enter")  # Press Enter

    # Type text
    agent.tools.os.keyboard_type("Hello, world!")
```

**Available Agent OS operations:**
- `click(button, repeat)` - Perform mouse clicks
- `mouse_move(x, y)` - Move mouse to coordinates
- `keyboard_tap(key, modifier_keys)` - Press keys with modifiers
- `keyboard_type(text)` - Type text strings
- `screenshot()` - Capture screen images

### Web Browser Control

The web browser tool, powered by Python's [webbrowser](https://docs.python.org/3/library/webbrowser.html) module, allows you to launch and control web browsers:

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    # Open URL in default browser
    agent.tools.webbrowser.open("http://www.google.com")

    # Open URL in new browser window
    agent.tools.webbrowser.open_new("http://www.example.com")

    # Open URL in new tab
    agent.tools.webbrowser.open_new_tab("http://www.github.com")
```

**Available methods:**
- `open(url)` - Open URL (may reuse existing window)
- `open_new(url)` - Open URL in new browser window
- `open_new_tab(url)` - Open URL in new browser tab

### Clipboard Management

The clipboard tool, powered by [pyperclip](https://github.com/asweigart/pyperclip), provides cross-platform clipboard access:

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    # Copy text to clipboard
    agent.tools.clipboard.copy("Hello, clipboard!")

    # Paste text from clipboard
    clipboard_content = agent.tools.clipboard.paste()
    print(f"Clipboard contains: {clipboard_content}")
```

**Available methods:**
- `copy(text)` - Copy text to clipboard
- `paste()` - Get text from clipboard

**Use cases:**
- Extract data from applications without direct API access
- Transfer data between applications
- Store intermediate results during multi-step workflows
- Share data with external scripts

### Multi-Monitor Support

For multi-monitor setups, specify which display the agent should control using the `display` parameter:

```python
from askui import ComputerAgent

# Control primary monitor (default)
with ComputerAgent(display=1) as agent:
    agent.click("Start button")

# Control secondary monitor
with ComputerAgent(display=2) as agent:
    agent.click("Application window")
```

**Important notes:**
- Display numbering starts at 1 (not 0)
- You may need to experiment to find the correct display number for your setup
- Better display detection tools are coming soon

### When to Use Direct Tools vs Agentic Commands

Choose the right approach based on your needs:

| Scenario | Use Direct Tools | Use Agentic Commands (`act()`) |
|----------|-----------------|--------------------------------|
| Precise coordinates known | ✅ `agent.tools.os.click()` | ❌ |
| UI element to locate | ❌ | ✅ `agent.click("Submit button")` |
| Simple, repeatable actions | ✅ | ❌ |
| Complex, multi-step workflows | ❌ | ✅ |
| Performance-critical operations | ✅ | ❌ |
| Adaptive to UI changes | ❌ | ✅ |
| Require no AI inference | ✅ | ❌ |

**Example combining both approaches:**

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    # Use agentic command to locate and click element
    agent.click("Login button")

    # Use direct tools for known, precise actions
    agent.tools.os.keyboard_type("user@example.com")
    agent.tools.os.keyboard_tap("tab")
    agent.tools.os.keyboard_type("password123")
    agent.tools.os.keyboard_tap("enter")

    # Extract result with AI
    result = agent.get("What's the welcome message?")
```

---

## Part 2: Extending with MCP

### What is MCP?

The Model Context Protocol (MCP) is a standardized way to provide context and tools to Large Language Models (LLMs). It acts as a universal interface - often described as "the USB-C port for AI" - that allows LLMs to connect to external resources and functionality in a secure, standardized manner.

MCP servers can:
- **Expose data** through `Resources` (similar to GET endpoints for loading information into the LLM's context)
- **Provide functionality** through `Tools` (similar to POST endpoints for executing code or producing side effects)
- **Define interaction patterns** through `Prompts` (reusable templates for LLM interactions)

For more information, see the [MCP specification](https://modelcontextprotocol.io/docs/getting-started/intro).

### MCP Concepts

MCP introduces three core concepts:

**1. Resources**
Resources provide read-only data to models. Think of them as GET endpoints that supply context:
- File contents
- Database records
- API responses
- Configuration data

**2. Tools**
Tools enable models to take actions and produce side effects. Think of them as POST endpoints:
- Execute commands
- Modify files
- Call external APIs
- Perform calculations

**3. Prompts**
Prompts are reusable templates that define common interaction patterns:
- Code review templates
- Data analysis workflows
- Testing scenarios

### Using MCP with AskUI Vision Agent

AskUI supports MCP tools through both the library (`ComputerAgent.act()`, `AndroidComputerAgent.act()`) and the Chat API. Tool usage comprises:
1. Listing available tools from MCP servers
2. Passing tool definitions to the model
3. Calling tools when the model requests them

The implementation uses [`fastmcp`](https://gofastmcp.com/getting-started/welcome) as the underlying MCP client.

#### With the Library

Integrate MCP tools directly into your agents by creating an MCP client and passing it to the `ToolCollection`:

```python
from fastmcp import Client
from fastmcp.mcp_config import MCPConfig, RemoteMCPServer

from askui import ComputerAgent
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


# Use with ComputerAgent
with ComputerAgent() as agent:
    agent.act(
        "Use the `test_stdio_server_test_stdio_tool`",
        tools=tools,
        on_message=on_message,
    )
```

**Important notes:**
- Tools are appended to the default tools of the agent, potentially overriding them
- Tool names are prefixed with the server name to avoid conflicts (e.g., `test_stdio_server_test_stdio_tool`)
- For different ways to construct `Client`s, see the [fastmcp documentation](https://gofastmcp.com/clients/client)

**Running the SSE Server Example:**

If you want to try the `test_sse_server`, start it before running your code:

```bash
python -m askui.tools.mcp.servers.sse
```

#### With Chat API

To use MCP servers with the Chat API, create MCP configurations. All agents will have access to configured servers if they can connect to them.

**Creating MCP Configs:**

MCP configurations can be created with either stdio or remote servers:

```bash
# Create stdio server configuration
curl -X 'POST' \
  'http://localhost:9261/v1/mcp-configs' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "test_stdio_server",
  "mcp_server": {
    "command": "python",
    "args": [
      "-m", "askui.tools.mcp.servers.stdio"
    ]
  }
}'

# Create remote SSE server configuration
curl -X 'POST' \
  'http://localhost:9261/v1/mcp-configs' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "test_sse_server",
  "mcp_server": {
    "url": "http://127.0.0.1:8001/sse/"
  }
}'
```

Each server must be created separately and is managed as a separate entity. For more endpoints to manage MCP configs, start the Chat API using `python -m askui.chat.api` and see the [Chat API documentation](http://localhost:9261/docs#/mcp-configs).

**Chat API Caveats:**

When using MCP through the Chat API, consider these limitations:

- **Configuration Limit**: Maximum of 100 MCP configurations allowed
- **Universal Availability**: All servers are currently passed to all available agents
- **No Filtering**: No way to filter servers or tools for specific use cases
- **Tool Name Prefixing**: Tool names are automatically prefixed with the MCP config ID
- **Server Availability**: When a server is unavailable, it is silently ignored

### Creating Custom MCP Servers

#### Different Frameworks

You can build MCP servers using various frameworks and languages.

**FastMCP (Python) - Recommended:**

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

**Official MCP SDKs:**

The official MCP specification provides SDKs for multiple languages:
[https://modelcontextprotocol.io/docs/sdk](https://modelcontextprotocol.io/docs/sdk)

### MCP Limitations and Best Practices

**Library Limitations:**

- **No Tool Selection/Filtering**: All MCP tools from connected servers are automatically available
- **Synchronous Code Requirement**: MCP tools must be run from within synchronous code contexts (no `async` or `await` allowed)
- **Limited Tool Response Content Types**: Only text and images (JPEG, PNG, GIF, WebP) are supported
- **Complexity Limits**: Tools are limited in number and complexity by the model's context window

**Best Practices:**

1. **Tool Design**:
   - Keep tools focused and single-purpose
   - Provide clear, descriptive names and documentation
   - Use Pydantic models for input validation
   - Return structured, parseable responses

2. **Server Configuration**:
   - Use meaningful server names to avoid tool name conflicts
   - Test servers independently before integrating with agents
   - Implement proper error handling and logging
   - Consider rate limiting for resource-intensive operations

3. **Security**:
   - Validate all inputs in your tool implementations
   - Avoid exposing sensitive operations without proper authorization
   - Use environment variables for credentials and secrets
   - Implement audit logging for critical operations

4. **Performance**:
   - Keep tool execution time under 30 seconds
   - Cache expensive operations when possible
   - Use async operations where appropriate (in server code)
   - Monitor resource usage and implement timeouts

---

## Part 3: Tool Store

### Overview

The Tool Store provides pre-built, ready-to-use tools that extend your agents' capabilities beyond the default computer control operations. These tools are organized by category and can be easily imported and integrated into your automation workflows.

### How to Use Pre-Built Tools

Import tools from `askui.tools.store` and pass them to your agent in one of two ways:

**Option 1: Pass tools to `agent.act()`:**

```python
from askui import ComputerAgent
from askui.tools.store.computer import ComputerSaveScreenshotTool
from askui.tools.store.universal import PrintToConsoleTool

with ComputerAgent() as agent:
    agent.act(
        "Take a screenshot and save it as demo/demo.png, then print a status message",
        tools=[
            ComputerSaveScreenshotTool(base_dir="./screenshots"),
            PrintToConsoleTool()
        ]
    )
```

**Option 2: Pass tools to the agent constructor:**

```python
from askui import ComputerAgent
from askui.tools.store.computer import ComputerSaveScreenshotTool
from askui.tools.store.universal import PrintToConsoleTool

with ComputerAgent(act_tools=[
    ComputerSaveScreenshotTool(base_dir="./screenshots"),
    PrintToConsoleTool()
]) as agent:
    agent.act("Take a screenshot and save it as demo/demo.png, then print a status message")
```

### Tool Categories

Tools are organized into three main categories based on their dependencies and use cases:

#### Universal Tools (`universal/`)

Work with any agent type, no special dependencies required.

**Examples:**
- `PrintToConsoleTool()` - Print messages to console output
- Data processing and formatting tools
- General utility functions

**Import from:** `askui.tools.store.universal`

#### Computer Tools (`computer/`)

Require `AgentOs` and work with `ComputerAgent` for desktop automation.

**Examples:**
- `ComputerSaveScreenshotTool(base_dir)` - Save screenshots to disk
- File operations (read, write, delete)
- System information retrieval
- Window management

**Import from:** `askui.tools.store.computer`

**Requirements:** Only available with `ComputerAgent`

#### Android Tools (`android/`)

Require `AndroidAgentOs` and work with `AndroidVisionAgent` for mobile automation.

**Examples:**
- Device information retrieval
- App management operations
- Mobile-specific interactions
- ADB command execution

**Import from:** `askui.tools.store.android`

**Requirements:** Only available with `AndroidVisionAgent`

---

## See Also

- **[02_Prompting.md](./02_Prompting.md)** - Guide AI agents with effective system prompts
- **[03_Using-Models-and-BYOM.md](./03_Using-Models-and-BYOM.md)** - Model selection and custom models
- **[04_Caching.md](./04_Caching.md)** - Record and replay actions for faster execution
- **[extracting-data.md](./extracting-data.md)** - Detailed guide on extracting structured data
- **[observability.md](./observability.md)** - Logging, reporting, and debugging
- **Examples**: Check the `examples/` directory for complete working code
- **Official Docs**: https://docs.askui.com
- **Discord Community**: https://discord.gg/Gu35zMGxbx
