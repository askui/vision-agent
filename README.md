# 🤖 AskUI Vision Agent

## 🔧 Setup

### 1. Install AskUI Agent OS

<details>
  <summary>Windows</summary>
  
  ##### AMD64

[AskUI Installer for AMD64](https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-Installer-Win-AMD64-Full.exe)

##### ARM64

[AskUI Installer for ARM64](https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-Installer-Win-ARM64-Full.exe)
</details>


<details>
  <summary>Linux</summary>

  **⚠️ Warning:** Agent OS currently does not work on Wayland. Switch to XOrg to use it.
  
##### AMD64

```shell
curl -o /tmp/AskUI-Suite-24.9.1-User-Installer-Linux-x64-Full.run https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-User-Installer-Linux-x64-Full.run
```
```shell
bash /tmp/AskUI-Suite-24.9.1-User-Installer-Linux-x64-Full.run
```

##### ARM64


```shell
curl -o /tmp/AskUI-Suite-24.9.1-User-Installer-Linux-ARM64-Full.run https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-User-Installer-Linux-ARM64-Full.run
```
```shell
bash /tmp/AskUI-Suite-24.9.1-User-Installer-Linux-ARM64-Full.run
```
</details>


<details>
  <summary>MacOS</summary>
  
```shell
curl -o /tmp/AskUI-Suite-24.9.1-User-Installer-MacOS-ARM64-Full.run https://files.askui.com/releases/Installer/24.9.1/AskUI-Suite-24.9.1-User-Installer-MacOS-ARM64-Full.run
```
```shell
bash /tmp/AskUI-Suite-24.9.1-User-Installer-MacOS-ARM64-Full.run
```
</details>


### 2. Install vision-agent in your Python environment

```shell
pip install askui
```

### 3. Authenticate with Anthropic

Set the `ANTHROPIC_API_KEY` environment variable to access the [Claude computer use model](https://docs.anthropic.com/en/docs/build-with-claude/computer-use). (Create a Anthropic key [here](https://console.anthropic.com/settings/keys))

<details>
  <summary>Linux & MacOS</summary>
  
  Use export to set an evironment variable:

  ```shell
  export ANTHROPIC_API_KEY=<your-api-key-here>
  ```
</details>

<details>
  <summary>Windows PowerShell</summary>
  
  Set an environment variable with $env:

  ```shell
  $env:ANTHROPIC_API_KEY="<your-api-key-here>"
  ```
</details>

## ▶️ Start Building

```python
from askui import VisionAgent

# Initialize your agent context manager
with VisionAgent() as agent:
    # Use the webbrowser tool to start browsing
    agent.tools.webbrowser.open_new("http://www.google.com")

    # Start to automate individual steps
    agent.click("url bar")
    agent.type("http://www.google.com")
    agent.keyboard("enter")

    # Extract information from the screen
    datetime = agent.get("What is the datetime at the top of the screen?")
    print(datetime)

    # Or let the agent work on its own
    agent.act("search for a flight from Berlin to Paris in January")
```


### 📜 Logging

You want a better understanding of what you agent is doing? Set the `log_level` to DEBUG.

```python
import logging

with VisionAgent(log_level=logging.DEBUG) as agent:
    agent...
```

### 🖥️ Multi-Monitor Support

You have multiple monitors? Choose which one to automate by setting `display` to 1 or 2.

```python
with VisionAgent(display=1) as agent:
    agent...
```