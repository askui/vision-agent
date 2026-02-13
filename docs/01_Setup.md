# Setup and Installation

This guide will get AskUI Vision Agent installed and configured on your system.

## Table of Contents

- [Python Package Installation](#python-package-installation)
- [AgentOS Installation](#agent-os-installation)
  - [Windows](#windows)
  - [Linux](#linux)
  - [MacOS](#macos)
- [Authentication and Configuration](#authentication-and-configuration)
- [Verifying Your Installation](#verifying-your-installation)
- [Troubleshooting](#troubleshooting)

## Python Package Installation

AskUI Vision Agent requires Python >=3.10, and <3.14.

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

## AgentOS Installation

AgentOS is a device controller that allows agents to take screenshots, move the mouse, click, type on the keyboard, interact with the shell, and manage user session across any operating system. It's installed on a Desktop OS but can also control mobile devices and HMI devices when connected.

### Windows

#### AMD64 (Intel/AMD Processors)

[Download AskUI Installer for AMD64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-AMD64-Web.exe)

#### ARM64 (ARM Processors)

[Download AskUI Installer for ARM64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-ARM64-Web.exe)

**Installation Steps:**
1. Download the installer for your architecture
2. Run the executable
3. Follow the installation wizard
4. AgentOS will start automatically after installation

### Linux

**⚠️ Important:** AgentOS currently does not work on Wayland. Switch to XOrg to use it.

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
4. AgentOS will start automatically after installation

### MacOS

**⚠️ Important:** AgentOS currently does not work on MacOS with Intel chips (x86_64/amd64 architecture). You need a Mac with Apple Silicon (M1, M2, M3, etc.).

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
5. AgentOS will start automatically after installation

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

#### AskUI Shell
_Note: The AskUI Shell can be installed using the AskUI Suite_
```powershell
askui-shell
AskUI-SetSetting -WorkspaceId <your-workspace-id-here> -Token <your-token-here>
```

## Verifying Your Installation

### Test Basic Functionality

Test that the Python package is installed correctly:

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    agent.click(button="left", repeat=2)
```

Run this with `python test.py`. If it double-clicks at the cursor location, your installation is working!

### Test AgentOS Connection

Verify that AgentOS is running and accessible:

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    # Take a screenshot to verify AgentOS connectivity
    agent.tools.os.screenshot()
    print("AgentOS is connected and working!")
```

### Test AI Agent Features

Verify that authentication is configured correctly:

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
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

### AgentOS Not Running

**Problem**: Error connecting to AgentOS

**Solutions**:
_tbd_

### Authentication Errors

**Problem**: `401 Unauthorized` or authentication errors

**Solutions**:
1. Verify your workspace ID and token are correct
2. Check that environment variables are set properly (`echo $ASKUI_WORKSPACE_ID` on Linux/Mac, `echo %ASKUI_WORKSPACE_ID%` on Windows)
3. Try setting credentials directly in code to isolate the issue
4. Verify your account is active at [hub.askui.com](https://hub.askui.com)

### Linux Wayland Issues

**Problem**: AgentOS not working on Linux

**Solution**: Switch from Wayland to XOrg:
1. Log out of your session
2. At the login screen, look for a gear icon or session type selector
3. Select "Ubuntu on Xorg" or similar X11 option
4. Log back in and try again

### MacOS Intel Issues

**Problem**: AgentOS not working on Intel Mac

**Solution**: AgentOS requires Apple Silicon (M1/M2/M3). You'll need to:
1. Use a Mac with Apple Silicon, or
2. Use a different operating system (Windows/Linux)

### Permission Issues (MacOS)

**Problem**: AgentOS can't control the screen or keyboard

**Solution**: Grant necessary permissions:
1. Open System Preferences → Security & Privacy → Privacy
2. Add AgentOS to:
   - Screen Recording
   - Accessibility
3. Restart AgentOS after granting permissions

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
