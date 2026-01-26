# 🤖 AskUI Vision Agent

[![Release Notes](https://img.shields.io/github/release/askui/vision-agent?style=flat-square)](https://github.com/askui/vision-agent/releases)
[![PyPI - License](https://img.shields.io/pypi/l/langchain-core?style=flat-square)](https://opensource.org/licenses/MIT)

**Enable AI agents to control your desktop (Windows, MacOS, Linux), mobile (Android, iOS) and HMI devices**

Join the [AskUI Discord](https://discord.gg/Gu35zMGxbx).

## Table of Contents

- [🤖 AskUI Vision Agent](#-askui-vision-agent)
  - [Table of Contents](#table-of-contents)
  - [📖 Introduction](#-introduction)
  - [📦 Installation](#-installation)
    - [AskUI Python Package](#askui-python-package)
    - [AskUI Agent OS](#askui-agent-os)
      - [AMD64](#amd64)
      - [ARM64](#arm64)
      - [AMD64](#amd64-1)
      - [ARM64](#arm64-1)
      - [ARM64](#arm64-2)
  - [🚀 Quickstart](#-quickstart)
    - [🧑 Control your devices](#-control-your-devices)
    - [🤖 Let AI agents control your devices](#-let-ai-agents-control-your-devices)
      - [🔐 Sign up with AskUI](#-sign-up-with-askui)
      - [⚙️ Configure environment variables](#️-configure-environment-variables)
      - [💻 Example](#-example)
    - [🛠️ Extending Agents with Tool Store](#️-extending-agents-with-tool-store)
  - [📚 Further Documentation](#-further-documentation)
  - [🤝 Contributing](#-contributing)
  - [📜 License](#-license)

## 📖 Introduction

AskUI Vision Agent is a powerful automation framework that enables you and AI agents to control your desktop, mobile, and HMI devices and automate tasks. With support for multiple AI models, multi-platform compatibility, and enterprise-ready features,

https://github.com/user-attachments/assets/a74326f2-088f-48a2-ba1c-4d94d327cbdf

**🎯 Key Features**

- Support for Windows, Linux, MacOS, Android and iOS device automation (Citrix supported)
- Support for single-step UI automation commands (RPA like) as well as agentic intent-based instructions
- In-background automation on Windows machines (agent can create a second session; you do not have to watch it take over mouse and keyboard)
- Flexible model use (hot swap of models) and infrastructure for reteaching of models (available on-premise)
- Secure deployment of agents in enterprise environments

## 📦 Installation

### AskUI Python Package

```shell
pip install askui[all]
```

**Requires Python >=3.10**

### AskUI Agent OS

Agent OS is a device controller that allows agents to take screenshots, move the mouse, click, and type on the keyboard across any operating system. It is installed on a Desktop OS but can control also mobile devices and HMI devices connected.

It offers powerful features like

- multi-screen support,
- support for all major operating systems (incl. Windows, MacOS and Linux),
- process visualizations,
- real Unicode character typing
- and more exciting features like application selection, in background automation and video streaming are to be released soon.

<details>
<summary>Windows</summary>

#### AMD64
[AskUI Installer for AMD64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-AMD64-Web.exe)

#### ARM64
[AskUI Installer for ARM64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-ARM64-Web.exe)

</details>

<details>
<summary>Linux</summary>
<br>

**⚠️ Warning:** Agent OS currently does not work on Wayland. Switch to XOrg to use it.

#### AMD64
```shell
curl -L -o /tmp/AskUI-Suite-Latest-User-Installer-Linux-AMD64-Web.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Linux-AMD64-Web.run
bash /tmp/AskUI-Suite-Latest-User-Installer-Linux-AMD64-Web.run
```

#### ARM64
```shell
curl -L -o /tmp/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Web.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Web.run
bash /tmp/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Web.run
```

</details>

<details>
<summary>MacOS</summary>
<br>

**⚠️ Warning:** Agent OS currently does not work on MacOS with Intel chips (x86_64/amd64 architecture). Switch to a Mac with Apple Silicon (arm64 architecture), e.g., M1, M2, M3, etc.

#### ARM64
```shell
curl -L -o /tmp/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Web.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Web.run
bash /tmp/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Web.run
```

</details>

## 🚀 Quickstart

### 🧑 Control your devices

Double click where-ever the cursor is currently at:

```python
from askui import VisionAgent

with VisionAgent() as agent:
    agent.click(button="left", repeat=2)
```

By default, the agent works within the context of a display that is selected which defaults to the primary display.

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
from askui import VisionAgent

with VisionAgent() as agent:
    # Give complex instructions to the agent (may have problems with virtual displays out of the box, so make sure there is no browser opened on a virtual display that the agent may not see)
    agent.act(
        "Look for a browser on the current device (checking all available displays, "
        "making sure window has focus),"
        " open a new window or tab and navigate to https://docs.askui.com"
        " and click on 'Search...' to open search panel. If the search panel is already "
        "opened, empty the search field so I can start a fresh search."
    )
    agent.type("Introduction")
    # Locates elements by text (you can also use images, natural language descriptions, coordinates, etc. to
    # describe what to click on)
    agent.click(
        "Documentation > Tutorial > Introduction",
    )
    first_paragraph = agent.get(
        "What does the first paragraph of the introduction say?"
    )
    print("\n--------------------------------")
    print("FIRST PARAGRAPH:\n")
    print(first_paragraph)
    print("--------------------------------\n\n")
```

Run the script with `python <file path>`, e.g `python test.py`.

If you see a lot of logs and the first paragraph of the introduction in the console, congratulations! You've successfully let AI agents control your device to automate a task! If you have any issues, please check the [documentation](https://docs.askui.com/01-tutorials/01-your-first-agent#common-issues-and-solutions) or join our [Discord](https://discord.gg/Gu35zMGxbx) for support.

### 🛠️ Extending Agents with Tool Store

The Tool Store provides optional tools to extend your agents' capabilities. Import tools from `askui.tools.store` and pass them to `agent.act()` or pass them to the agent constructor as `act_tools`.

**Example passing tools to `agent.act()`:**
```python
from askui import VisionAgent
from askui.tools.store.computer import ComputerSaveScreenshotTool
from askui.tools.store.universal import PrintToConsoleTool

with VisionAgent() as agent:
    agent.act(
        "Take a screenshot and save it as demo/demo.png, then print a status message",
        tools=[
            ComputerSaveScreenshotTool(base_dir="./screenshots"),
            PrintToConsoleTool()
        ]
    )
```

**Example passing tools to the agent constructor:**
```python
from askui import VisionAgent
from askui.tools.store.computer import ComputerSaveScreenshotTool
from askui.tools.store.universal import PrintToConsoleTool

with VisionAgent(act_tools=[
    ComputerSaveScreenshotTool(base_dir="./screenshots"),
    PrintToConsoleTool()
]) as agent:
    agent.act("Take a screenshot and save it as demo/demo.png, then print a status message")
```

Tools are organized by category: `universal/` (work with any agent), `computer/` (require `AgentOs`) works  only with VisionAgent and `android/` (require `AndroidAgentOs`) works only with AndroidVisionAgent.

## 📚 Further Documentation

Aside from our [official documentation](https://docs.askui.com), we also have some additional guides and examples under the [docs](docs) folder that you may find useful, for example:

- **[Chat](docs/chat.md)** - How to interact with agents through a chat
- **[Direct Tool Use](docs/direct-tool-use.md)** - How to use the tools, e.g., clipboard, the Agent OS etc.
- **[Extracting Data](docs/extracting-data.md)** - How to extract data from the screen and documents
- **[MCP](docs/mcp.md)** - How to use MCP servers to extend the capabilities of an agent
- **[Observability](docs/observability.md)** - Logging and reporting
- **[Telemetry](docs/telemetry.md)** - Which data we gather and how to disable it
- **[Using Models](docs/using-models.md#using-custom-models)** - How to use different models including how to register your own custom models

## 🤝 Contributing

We'd love your help! Contributions, ideas, and feedback are always welcome. A proper contribution guide is coming soon—stay tuned!


## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
