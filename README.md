# 🤖 AskUI Python SDK

[![Release Notes](https://img.shields.io/github/release/askui/vision-agent?style=flat-square)](https://github.com/askui/vision-agent/releases)
[![PyPI - License](https://img.shields.io/pypi/l/langchain-core?style=flat-square)](https://opensource.org/licenses/MIT)

**Enable AI agents to control your desktop (Windows, MacOS, Linux), mobile (Android, iOS) and HMI devices**

Join the [AskUI Discord](https://discord.gg/Gu35zMGxbx).

## Why AskUI?

Traditional UI automation is fragile. Every time a button moves, a label changes, or a layout shifts, your scripts break. You're stuck maintaining brittle selectors, writing conditional logic for edge cases, and constantly updating tests.

**AskUI Agents solve this by combining two powerful approaches:**

1. **Vision-based automation** - Find UI elements by what they look like or say, not by brittle XPath or CSS selectors
2. **AI-powered agents** - Give high-level instructions and let AI figure out the steps
AskUI Python SDK is a powerful automation framework that enables you and AI agents to control your desktop, mobile, and HMI devices and automate tasks. With support for multiple AI models, multi-platform compatibility, and enterprise-ready features,

Whether you're automating desktop apps, testing mobile applications, or building RPA workflows, AskUI adapts to UI changes automatically—saving you hours of maintenance work.

## Key Features

- **Multi-platform** - Works on Windows, Linux, MacOS, and Android
- **Two modes** - Single-step UI commands or agentic intent-based instructions
- **Vision-first** - Find elements by text, images, or natural language descriptions
- **Model flexibility** - Anthropic Claude, Google Gemini, AskUI models, or bring your own
- **Extensible** - Add custom tools and capabilities via Model Context Protocol (MCP)
- **Caching** - Save expensive calls to AI APIs by using them only when really necessary

## Quick Examples

### Programmatic UI Automation

Control your devices with simple, vision-based commands:

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    # Click on a button by its text
    agent.click("Submit")

    # Type into the currently focused field
    agent.type("hello@example.com")

    # Click at specific coordinates
    agent.click(x=100, y=200)

    # Find and click an element by image
    agent.click(image="./assets/login-button.png")
```

### Agentic UI Automation

Run the script with `python <file path>`, e.g `python test.py` to see if it works.

### 🤖 Let AI agents control your devices

In order to let AI agents control your devices, you need to be able to connect to an AI model (provider). We host some models ourselves and support several other ones, e.g. Anthropic, OpenRouter, Hugging Face, etc. out of the box. If you want to use a model provider or model that is not supported, you can easily plugin your own (see [Custom Models](docs/using-models.md#using-custom-models)).

For this example, we will us AskUI as the model provider to easily get started.

#### 🔐 Sign up with AskUI

Sign up at [hub.askui.com](https://hub.askui.com) to:
- Activate your **free trial** by signing up (no credit card required)
- Get your workspace ID and access token

#### ⚙️ Configure environment variables

<details>
<summary>Linux & MacOS</summary>

```shell
export ASKUI_WORKSPACE_ID=<your-workspace-id-here>
export ASKUI_TOKEN=<your-token-here>
```
</details>

<details>
<summary>Windows PowerShell</summary>

```shell
$env:ASKUI_WORKSPACE_ID="<your-workspace-id-here>"
$env:ASKUI_TOKEN="<your-token-here>"
```

</details>

#### 💻 Example

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    # Complex multi-step instruction
    agent.act(
        "Open a browser, navigate to GitHub, search for 'askui vision-agent', "
        "and star the repository"
    )

    # Extract information from the screen
    balance = agent.get("What is my current account balance?")
    print(f"Balance: {balance}")

    # Combine both approaches
    agent.act("Find the login form")
    agent.type("user@example.com")
    agent.click("Next")
```

### Extend with Custom Tools

Add new capabilities to your agents:

```python
from askui import ComputerAgent
from askui.tools.store.computer import ComputerSaveScreenshotTool
from askui.tools.store.universal import PrintToConsoleTool

with ComputerAgent() as agent:
    agent.act(
        "Take a screenshot of the current screen and save it, then confirm",
        tools=[
            ComputerSaveScreenshotTool(base_dir="./screenshots"),
            PrintToConsoleTool()
        ]
    )
```

## Getting Started

Ready to build your first agent? Check out our documentation:

1. **[Start Here](docs/00_Overview.md)** - Overview and core concepts
2. **[Setup](docs/01_Setup.md)** - Installation and configuration
3. **[System Prompts](docs/02_Prompting.md)** - How to write effective instructions
4. **[Models](docs/03_Using-Models-and-BYOM.md)** - Using and customizing AI models
5. **[Caching](docs/04_Caching.md)** - Optimize performance and costs
6. **[Tools](docs/05_Tools.md)** - Extend agent capabilities
7. **[Observability](docs/06_Observability-Telemetry-Tracing.md)** - Monitor and debug agents

**Additional guides:**
- [Extracting Data](docs/extracting-data.md) - Extract structured data from screens and documents
- [File Support](docs/file-support.md) - Work with PDFs, images, and other file types

**Official documentation:** [docs.askui.com](https://docs.askui.com)

## Quick Install

```bash
pip install askui[all]
```

**Requires Python >=3.10**

You'll also need to install AskUI Agent OS for device control. See [Setup Guide](docs/01_Setup.md) for detailed instructions.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
