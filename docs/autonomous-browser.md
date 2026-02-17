# Autonomous Agent Action-Taking Web Browser

The AskUI Autonomous Browser provides a dev-centric interface for web automation and autonomous agent interactions. It allows you to run tasks directly from the CLI, record workflows, and replay them later with enhanced intelligence and heuristics.

## Table of Contents

- [Quickstart](#quickstart)
- [Web UI & Remote Control](#web-ui--remote-control)
- [CLI Usage](#cli-usage)
  - [Run Command](#run-command)
  - [UI Command](#ui-command)
  - [Workflow Command](#workflow-command)
- [MCP Integration](#mcp-integration)
- [Developer Info](#developer-info)

## Quickstart

Start an interactive autonomous browser session:

```bash
python -m askui.browser run --url https://google.com
```

## Web UI & Remote Control

The AskUI Autonomous Browser features a built-in Web UI that provides a live view of the agent's actions and allows for remote control.

To launch the UI:
```bash
python -m askui.browser ui
```
Then navigate to `http://127.0.0.1:8000` in your browser.

**Features:**
- **Live View**: See exactly what the agent sees through frequent screenshot updates.
- **Remote Control**: Click anywhere on the browser view to send a remote click to the agent.
- **Remote Type**: Use the "Type Text" button to input text at the current focus.
- **LLM Instructions**: Give natural language instructions to the agent through the chat interface.
- **Heuristic Recovery**: Use the "Solve Common Hurdles" button to instruct the agent to clear popups and cookie banners.

## CLI Usage

The CLI is accessible via `python -m askui.browser`.

### Run Command

Execute a single task or enter interactive mode.

- **Interactive Mode**: `python -m askui.browser run`
- **Single Task**: `python -m askui.browser run "Search for AskUI on Google"`
- **Headed/Headless**: Use `--headed` (default) or `--headless`.
- **Verbose Mode**: Use `--verbose` to see the agent's internal reasoning loop (Plan -> Execute -> Verify) and heuristic decision making.

### UI Command

Launch the web-based remote control interface.

```bash
python -m askui.browser ui [--port 8000] [--host 127.0.0.1]
```

### Workflow Command

Create and manage re-usable autonomous workflows.

- **Record a Workflow**:
  ```bash
  python -m askui.browser workflow record my_workflow.json --url https://docs.askui.com
  ```
  Follow the prompts to enter steps. Type `save` to finish.

- **Replay a Workflow**:
  ```bash
  python -m askui.browser workflow replay my_workflow.json
  ```

Workflows are saved as JSON files using the AskUI `Scenario` model. Replay mode automatically uses heuristic recovery (e.g., attempt to close obstructing popups) if a step fails.

## MCP Integration

The AskUI Chat API now includes a **Web MCP Server**, allowing other MCP-compatible clients to control the browser using AskUI tools.

To use the Web MCP tools:
1. Start the Chat API: `python -m askui.chat`
2. Connect your MCP client to the server (default port `9261`).

Available tools include:
- `playwright_goto_tool`
- `playwright_back_tool`
- `playwright_forward_tool`
- `playwright_get_page_title_tool`
- `playwright_get_page_url_tool`

## Developer Info

### Advanced Intelligence & Heuristics
The browser agent follows a **Plan -> Execute -> Verify** loop. It intelligently handles:
- **Cookie Banners & Popups**: Automatically identifying and closing obstructions.
- **Dynamic Content**: Heuristic waiting and scrolling to find elements.
- **Self-Correction**: Diagnosing failures and retrying with alternative strategies.
- **Deterministic Replay**: Enhanced instructions ensure the agent verifies each step during workflow replay.
