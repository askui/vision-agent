# Overview

## Why AskUI Vision Agent?

AskUI Vision Agent is a powerful automation framework that bridges the gap between human intent and computer control. Whether you need precise UI automation for testing, want AI agents to handle complex workflows, or need to automate tasks across desktop, mobile, and HMI devices, AskUI Vision Agent provides a unified solution.

### The Problem

Traditional automation frameworks require:
- Brittle selectors that break when UI changes
- Separate tools for different platforms (web, desktop, mobile)
- Manual scripting of every action step
- Constant maintenance as applications evolve
- Random application behavior
- External issues like network, rights or installation issues

### The Solution

AskUI Vision Agent offers two complementary approaches:

*1. Agentic Control (Goal-based)**
```python
with VisionAgent() as agent:
    agent.act(
        "Search for flights from New York to London, "
        "filter by direct flights, and show me the cheapest option"
    )

Natural language instructions where AI agents autonomously navigate UI, make decisions, and achieve goals. Perfect for complex workflows and exploratory testing.

### Key Capabilities

- **Multi-Platform**: Windows, MacOS, Linux, Android, Citric & KVM
- **Vision-Powered**: Uses AI models to understand UI visually, no selectors needed
- **Flexible Models**: Hot-swap between models, use AskUI-hosted, Anthropic, OpenRouter, or bring your own
- **Extensible**: Custom tools via MCP, custom models, custom prompts

## How This Documentation Is Structured

This documentation is organized to take you from setup to advanced usage:

### 01 - Setup
**Topics**: Installation, Agent OS setup, environment configuration, authentication

Start here to get AskUI Vision Agent installed and running. Covers Python package installation and the Agent OS component that enables cross-platform device control.

### 02 - Prompting
**Topics**: System prompts, customizing agent behavior, prompt engineering best practices

Learn how to guide AI agents with effective prompts. Critical for the `act()` method and achieving reliable agentic behavior.

### 03 - Using Models and BYOM
**Topics**: Model selection, available models, model composition, bringing your own model

Understand the model system, how to choose models for different tasks, and how to integrate custom models or third-party providers.

### 04 - Caching
**Topics**: Recording trajectories, replaying actions, regression testing

Speed up test execution and improve reliability by recording and replaying successful action sequences.

### 05 - Tools
**Topics**: Direct tool use, Model Context Protocol (MCP), custom tools, extending agents

Access low-level tools directly, integrate external services via MCP, and extend agent capabilities with custom tools.

### 06 - Observability, Telemetry, Tracing
**Topics**: Reporting, debugging, telemetry, OpenTelemetry tracing, monitoring

Track agent behavior, debug issues, and monitor performance in production environments.

## Additional Resources

- **Extracting Data**: See `extracting-data.md` for detailed guide on using `get()` to extract structured data
- **File Support**: See `file-support.md` for working with PDFs, Excel, Word documents
- **Examples**: Check the `examples/` directory for complete working code
- **GitHub Issues**: https://github.com/askui/vision-agent/issues
- **Official Docs**: https://docs.askui.com

## Quick Start Example

Here's a complete example to get you started:

```python
import os
from askui import ComputerAgent

# Set your credentials (sign up at https://www.askui.com)
os.environ["ASKUI_WORKSPACE_ID"] = "<your-workspace-id>"
os.environ["ASKUI_TOKEN"] = "<your-token>"

# Programmatic approach
with ComputerAgent() as agent:
    agent.click("Login button")
    agent.type("user@example.com")
    agent.click("Password field")
    agent.type("password123")
    agent.click("Submit")

    # Extract data
    welcome_message = agent.get("What's the welcome message?")
    print(welcome_message)

# Agentic approach
with ComputerAgent() as agent:
    agent.act(
        "Log in with email 'user@example.com' and password 'password123', "
        "then tell me what the welcome message says"
    )
```

## Next Steps

1. **[01_Setup.md](./01_Setup.md)** - Install AskUI Vision Agent and Agent OS
2. **[02_Prompting.md](./02_Prompting.md)** - Learn to guide AI agents effectively
3. **[03_Using-Models-and-BYOM.md](./03_Using-Models-and-BYOM.md)** - Choose and customize models

Let's get started! 🚀
