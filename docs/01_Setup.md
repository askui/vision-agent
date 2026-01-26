# Setup and Installation

This guide will get AskUI Vision Agent installed and configured on your system.

## Table of Contents

- [Python Package Installation](#python-package-installation)
- [Agent OS Installation](#agent-os-installation)
  - [Windows](#windows)
  - [Linux](#linux)
  - [MacOS](#macos)
- [Authentication and Configuration](#authentication-and-configuration)
- [Verifying Your Installation](#verifying-your-installation)
- [Troubleshooting](#troubleshooting)

## Python Package Installation

AskUI Vision Agent requires Python 3.10 or higher.

```bash
pip install askui[all]
```

This installs:
- Core AskUI Vision Agent library
- All optional dependencies for full functionality
- Support for different file formats (PDFs, Excel, Word)
- All model provider integrations

### Alternative: Minimal Installation

If you want a minimal installation without optional dependencies:

```bash
pip install askui
```

You can then install specific extras as needed:

```bash
pip install askui[anthropic]  # Anthropic Claude support
pip install askui[openrouter]  # OpenRouter support
pip install askui[documents]  # PDF, Excel, Word support
```

## Agent OS Installation

Agent OS is a device controller that allows agents to take screenshots, move the mouse, click, and type on the keyboard across any operating system. It's installed on a Desktop OS but can also control mobile devices and HMI devices when connected.

### Windows

#### AMD64 (Intel/AMD Processors)

[Download AskUI Installer for AMD64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-AMD64-Web.exe)

#### ARM64 (ARM Processors)

[Download AskUI Installer for ARM64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-ARM64-Web.exe)

**Installation Steps:**
1. Download the installer
2. Run the executable
3. Follow the installation wizard
4. Agent OS will start automatically after installation

### Linux

**⚠️ Important:** Agent OS currently does not work on Wayland. Switch to XOrg to use it.

#### AMD64 (Intel/AMD Processors)

```bash
curl -L -o /tmp/AskUI-Suite-Latest-User-Installer-Linux-AMD64-Web.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Linux-AMD64-Web.run
bash /tmp/AskUI-Suite-Latest-User-Installer-Linux-AMD64-Web.run
```

#### ARM64 (ARM Processors)

```bash
curl -L -o /tmp/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Web.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Web.run
bash /tmp/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Web.run
```

**Installation Steps:**
1. Download the installer script
2. Run the script with bash
3. Follow the prompts
4. Agent OS will start automatically after installation

### MacOS

**⚠️ Important:** Agent OS currently does not work on MacOS with Intel chips (x86_64/amd64 architecture). You need a Mac with Apple Silicon (M1, M2, M3, etc.).

#### ARM64 (Apple Silicon)

```bash
curl -L -o /tmp/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Web.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Web.run
bash /tmp/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Web.run
```

**Installation Steps:**
1. Download the installer script
2. Run the script with bash
3. Follow the prompts
4. Grant necessary permissions when prompted (screen recording, accessibility)
5. Agent OS will start automatically after installation

## Authentication and Configuration

To use AI agent features (like `agent.act()`), you need to sign up and configure your credentials.

### 1. Sign Up

Sign up at [hub.askui.com](https://hub.askui.com) to:
- Activate your **free trial** (no credit card required)
- Get your workspace ID and access token

### 2. Configure Environment Variables

Set your credentials as environment variables so AskUI Vision Agent can authenticate with the service.

#### Linux & MacOS

```bash
export ASKUI_WORKSPACE_ID=<your-workspace-id-here>
export ASKUI_TOKEN=<your-token-here>
```

To make these permanent, add them to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
echo 'export ASKUI_WORKSPACE_ID=<your-workspace-id>' >> ~/.bashrc
echo 'export ASKUI_TOKEN=<your-token>' >> ~/.bashrc
source ~/.bashrc
```

#### Windows PowerShell

```powershell
$env:ASKUI_WORKSPACE_ID="<your-workspace-id-here>"
$env:ASKUI_TOKEN="<your-token-here>"
```

To make these permanent, add them to your PowerShell profile or set them as system environment variables via System Properties.

#### Windows Command Prompt

```cmd
set ASKUI_WORKSPACE_ID=<your-workspace-id-here>
set ASKUI_TOKEN=<your-token-here>
```

### 3. Alternative: Configuration in Code

You can also set credentials directly in your Python code (not recommended for production):

```python
import os

os.environ["ASKUI_WORKSPACE_ID"] = "<your-workspace-id>"
os.environ["ASKUI_TOKEN"] = "<your-token>"

from askui import VisionAgent

with VisionAgent() as agent:
    agent.act("Your task here")
```

## Verifying Your Installation

### Test Basic Functionality

Test that the Python package is installed correctly:

```python
from askui import VisionAgent

with VisionAgent() as agent:
    agent.click(button="left", repeat=2)
```

Run this with `python test.py`. If it double-clicks at the cursor location, your installation is working!

### Test Agent OS Connection

Verify that Agent OS is running and accessible:

```python
from askui import VisionAgent

with VisionAgent() as agent:
    # Take a screenshot to verify Agent OS connectivity
    agent.tools.os.screenshot()
    print("Agent OS is connected and working!")
```

### Test AI Agent Features

Verify that authentication is configured correctly:

```python
from askui import VisionAgent

with VisionAgent() as agent:
    agent.act(
        "Open a browser, navigate to https://docs.askui.com, "
        "and click on 'Search...'"
    )
    agent.type("Introduction")
    agent.click("Documentation > Tutorial > Introduction")

    first_paragraph = agent.get(
        "What does the first paragraph of the introduction say?"
    )
    print(f"First paragraph: {first_paragraph}")
```

If this runs successfully and prints the first paragraph, congratulations! Your setup is complete.

## Troubleshooting

### Agent OS Not Running

**Problem**: Error connecting to Agent OS

**Solutions**:
1. Check if Agent OS is running (look for the system tray icon)
2. Restart Agent OS from your applications menu
3. Reinstall Agent OS if the problem persists

### Authentication Errors

**Problem**: `401 Unauthorized` or authentication errors

**Solutions**:
1. Verify your workspace ID and token are correct
2. Check that environment variables are set properly (`echo $ASKUI_WORKSPACE_ID` on Linux/Mac, `echo %ASKUI_WORKSPACE_ID%` on Windows)
3. Try setting credentials directly in code to isolate the issue
4. Verify your account is active at [hub.askui.com](https://hub.askui.com)

### Python Version Issues

**Problem**: Import errors or compatibility issues

**Solutions**:
1. Check your Python version: `python --version` (must be 3.10 or higher)
2. Create a virtual environment to isolate dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install askui[all]
   ```

### Linux Wayland Issues

**Problem**: Agent OS not working on Linux

**Solution**: Switch from Wayland to XOrg:
1. Log out of your session
2. At the login screen, look for a gear icon or session type selector
3. Select "Ubuntu on Xorg" or similar X11 option
4. Log back in and try again

### MacOS Intel Issues

**Problem**: Agent OS not working on Intel Mac

**Solution**: Agent OS requires Apple Silicon (M1/M2/M3). You'll need to:
1. Use a Mac with Apple Silicon, or
2. Use a different operating system (Windows/Linux)

### Permission Issues (MacOS)

**Problem**: Agent OS can't control the screen or keyboard

**Solution**: Grant necessary permissions:
1. Open System Preferences → Security & Privacy → Privacy
2. Add Agent OS to:
   - Screen Recording
   - Accessibility
3. Restart Agent OS after granting permissions

## Next Steps

Now that you're set up, learn how to guide AI agents effectively:

- **[02_Prompting.md](./02_Prompting.md)** - System prompts and prompt engineering
- **[03_Using-Models-and-BYOM.md](./03_Using-Models-and-BYOM.md)** - Choose and customize models
- **[05_Tools.md](./05_Tools.md)** - Extend agent capabilities with tools

## Getting Help

If you encounter issues not covered here:

- **Official Documentation**: https://docs.askui.com/01-tutorials/01-your-first-agent#common-issues-and-solutions
- **Discord Community**: https://discord.gg/Gu35zMGxbx
- **GitHub Issues**: https://github.com/askui/vision-agent/issues
