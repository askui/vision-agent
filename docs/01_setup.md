# Setup and Installation

This guide will get AskUI Vision Agent installed and configured on your system.

## Python Package Installation

AskUI Vision Agent requires Python >=3.10, and <3.14.

For installing the python-sdk please run

```bash
pip install askui[all]
```

This installs the core AskUI Vision Agent library together with optional dependencies (see `pyproject.toml`) for full functionality, including:
- Android automation
- Support for different file formats (PDFs, Excel, Word)
- All model provider integrations

If you want a minimal installation without optional dependencies, please run

```bash
pip install askui
```

## AgentOS Installation

AgentOS is a device controller that allows agents to take screenshots, move the mouse, click, type on the keyboard, interact with the shell, and manage user session across any operating system. It's installed on a Desktop OS but can also control mobile devices and HMI devices when connected.

### Windows

- [Download AskUI Installer for AMD64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-AMD64-Web.exe)
- [Download AskUI Installer for ARM64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-ARM64-Web.exe)

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

To use the AskUI VisionAgent, please sign up and configure your credentials.

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

In case you encounter `401 Unauthorized` or authentication errors:

1. Verify your workspace ID and token are correct
2. Check that environment variables are set properly (`echo $ASKUI_WORKSPACE_ID` on Linux/Mac, `echo %ASKUI_WORKSPACE_ID%` on Windows)
3. Verify your account is active at [hub.askui.com](https://hub.askui.com)


## Getting Help

If you encounter issues not covered here:

- **Official Documentation**: https://docs.askui.com/01-tutorials/01-your-first-agent#common-issues-and-solutions
- **Discord Community**: https://discord.gg/Gu35zMGxbx
- **GitHub Issues**: https://github.com/askui/vision-agent/issues
