# 🤖 AskUI Vision Agent

⚡ Automate computer tasks in Python ⚡

[![Release Notes](https://img.shields.io/github/release/askui/vision-agent?style=flat-square)](https://github.com/askui/vision-agent/releases)
[![PyPI - License](https://img.shields.io/pypi/l/langchain-core?style=flat-square)](https://opensource.org/licenses/MIT)

Join the [AskUI Discord](https://discord.gg/Gu35zMGxbx).

## 🔧 Setup

### 1. Install AskUI Agent OS

Agent OS is a device controller that allows agents to take screenshots, move the mouse, click, and type on the keyboard across any operating system.

<details>
  <summary>Windows</summary>
  
  ##### AMD64

[AskUI Installer for AMD64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-Installer-Win-AMD64-Full.exe)

##### ARM64

[AskUI Installer for ARM64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-Installer-Win-ARM64-Full.exe)
</details>


<details>
  <summary>Linux</summary>

  **⚠️ Warning:** Agent OS currently does not work on Wayland. Switch to XOrg to use it.
  
##### AMD64

```shell
curl -o /tmp/AskUI-Suite-Latest-User-Installer-Linux-x64-Full.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Linux-x64-Full.run
```
```shell
bash /tmp/AskUI-Suite-Latest-User-Installer-Linux-x64-Full.run
```

##### ARM64


```shell
curl -o /tmp/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Full.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Full.run
```
```shell
bash /tmp/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Full.run
```
</details>


<details>
  <summary>MacOS</summary>
  
```shell
curl -o /tmp/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Full.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Full.run
```
```shell
bash /tmp/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Full.run
```
</details>


### 2. Install vision-agent in your Python environment

```shell
pip install askui
```

**Note:** Requires Python version >=3.10.

### 3a. Authenticate with an Automation Model Provider

|  | AskUI [INFO](https://app.askui.com/) | Anthropic [INFO](https://console.anthropic.com/settings/keys) |
|----------|----------|----------|
| ENV Variables    | `ASKUI_WORKSPACE_ID`, `ASKUI_TOKEN`   | `ANTHROPIC_API_KEY`   |
| Supported Commands    | `click()`   | `click()`, `get()`, `act()`   |
| Description    | Faster Inference, European Server, Enterprise Ready   | Supports complex actions   |

To get started, set the environment variables required to authenticate with your chosen model provider.

#### How to set an environment variable?
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


### 3b. Test with 🤗 Hugging Face Model Demos

You can test the Vision Agent with Hugging Face models via their Spaces API. Please note that the API is rate-limited so for production use cases, it is recommended to choose step 3a.

**Note:** Hugging Face Spaces host model demos provided by individuals not associated with Hugging Face or AskUI. Don't use these models on screens with sensible information.

**Supported Models:**
- `AskUI/PTA-1`
- `OS-Copilot/OS-Atlas-Base-7B`
- `showlab/ShowUI-2B`
- `Qwen/Qwen2-VL-2B-Instruct`
- `Qwen/Qwen2-VL-7B-Instruct`

**Example Code:**
```python
agent.click("search field", model_name="OS-Copilot/OS-Atlas-Base-7B")
```


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

### 🎛️ Model Selection

Instead of relying on the default model for the entire automation script, you can specify a model for each `click` command using the `model_name` parameter.

|  | AskUI | Anthropic |
|----------|----------|----------|
| `click()`    | `askui-combo`, `askui-pta`, `askui-ocr`   | `anthropic-claude-3-5-sonnet-20241022`   |

**Example:** `agent.click("Preview", model_name="askui-combo")`

### 🛠️ Direct Tool Use

Under the hood agents are using a set of tools. You can also directly access these tools.

#### Agent OS

The controller for the operating system.

```python
agent.tools.os.click("left", 2) # clicking
agent.tools.os.mouse(100, 100) # mouse movement
agent.tools.os.keyboard_tap("v", modifier_keys=["control"]) # Paste
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
