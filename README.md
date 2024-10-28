# vision-agent

## Setup

### 1. Install AskUI Controller

<details>
  <summary>Windows</summary>
  
  ##### AMD64

[AskUI Installer for AMD64](https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-Installer-Win-AMD64-Full.exe)

##### ARM64

[AskUI Installer for ARM64](https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-Installer-Win-ARM64-Full.exe)
</details>


<details>
  <summary>Linux</summary>
  
##### AMD64

`curl -o /tmp/AskUI-Suite-24.9.1-User-Installer-Linux-x64-Full.run https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-User-Installer-Linux-x64-Full.run`

`bash /tmp/AskUI-Suite-24.9.1-User-Installer-Linux-x64-Full.run`

##### ARM64

`curl -o /tmp/AskUI-Suite-24.9.1-User-Installer-Linux-ARM64-Full.run https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-User-Installer-Linux-ARM64-Full.run`

`bash /tmp/AskUI-Suite-24.9.1-User-Installer-Linux-ARM64-Full.run`
</details>


<details>
  <summary>MacOs</summary>
  
`curl -o /tmp/AskUI-Suite-24.9.1-User-Installer-MacOS-ARM64-Full.run https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-User-Installer-MacOS-ARM64-Full.run`

`bash /tmp/AskUI-Suite-24.9.1-User-Installer-MacOS-ARM64-Full.run`
</details>


### 2. Install vision-agent in your Python environment

`pip install git+https://github.com/askui/vision-agent.git`

### 3. Set Controller Environment

`export ASKUI_INSTALL_DIRECTORY=<path>/.askui-suites`

### 4. Authenticate with Anthropic

`export ANTHROPIC_API_KEY=<your-api-key-here>`

## Start Building

```python
from vision_agent import VisionAgent

# Initialize your agent
agent = VisionAgent()

# Launch you target application via CLI
agent.cli("firefox")

# Start to automate individual steps
agent.click("url bar")
agent.type("http://www.google.com")
agent.keyboard("enter")

# Or let the agent work on its own
agent.act("search for a flight from Berlin to Paris in January")

# Close agent when done
agent.close()
```
