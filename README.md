# 🤖 AskUI Vision Agent

⚡ Automate computer tasks in Python ⚡

[![Release Notes](https://img.shields.io/github/release/askui/vision-agent?style=flat-square)](https://github.com/askui/vision-agent/releases)
[![PyPI - License](https://img.shields.io/pypi/l/langchain-core?style=flat-square)](https://opensource.org/licenses/MIT)

Join the [AskUI Community](https://community.askui.com).

## 🔧 Setup

### 1. Install AskUI Agent OS

Agent OS is a device controller that allows agents to take screenshots, move the mouse, click, and type on the keyboard across any operating system.

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

### 🛠️ Direct Tool Use

Under the hood agents are using a set of tools. You can also directly access these tools.

#### Agent OS

The controller for the operating system.

```python
agent.tools.os.click("left", 2) # clicking
agent.tools.os.mouse(100, 100) # mouse movement
# and many more
```

#### Web browser

The webbrowser tool powered by [webbrowser](https://docs.python.org/3/library/webbrowser.html) allows you to directly access webbrowsers in your environment.

```python
agent.tools.webbrowser.open_new("http://www.google.com")
# also check out open and open_new_tab
```

#### Clipboard

The clipboard tool powered by [pyperclip](https://github.com/asweigart/pyperclip) allows you to interact with the clipboard.

```python
agent.tools.clipboard.copy("...")
result = agent.tools.clipboard.paste()
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


## What is AskUI Vision Agent?

**AskUI Vision Agent** is a versatile AI powered framework that enables you to automate computer tasks in Python. 

It connects Agent OS with powerful computer use models like Anthropic's Claude Sonnet 3.5 v2 and the AskUI Prompt-to-Action series. It is your entry point for building complex automation scenarios with detailed instructions or let the agent explore new challenges on its own. 


![image](docs/assets/Architecture.svg)


**Agent OS** is a custom-built OS controller designed to enhance your automation experience.

 It offers powerful features like 
 - multi-screen support,
 - support for all major operating systems (incl. Windows, MacOS and Linux),
 - process visualizations,
 - real Unicode character typing

and more exciting features like application selection, in background automation and video streaming are to be released soon.
