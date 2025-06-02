# 🤖 Enable AI to control your desktop, mobile and HMI devices

**We make Windows, MacOS, Linux,  Android an iOS accessible for AI agents by finding any element on screen.**

Key features of AskUI include:

- Support for Windows, Linux, MacOS, Android and iOS device automation (Citrix supported)
- Support for single-step UI automation commands (RPA like) as well as agentic intent-based instructions
- In-background automation on Windows machines (agent can create a second session; you do not have to watch it take over mouse and keyboard)
- Flexible model use (hot swap of models) and infrastructure for reteaching of models (available on-premise)
- Secure deployment of agents in enterprise environments

[![Release Notes](https://img.shields.io/github/release/askui/vision-agent?style=flat-square)](https://github.com/askui/vision-agent/releases)
[![PyPI - License](https://img.shields.io/pypi/l/langchain-core?style=flat-square)](https://opensource.org/licenses/MIT)

Join the [AskUI Discord](https://discord.gg/Gu35zMGxbx).

https://github.com/user-attachments/assets/a74326f2-088f-48a2-ba1c-4d94d327cbdf


## 🔧 Setup

### 1. Install AskUI Agent OS

Agent OS is a device controller that allows agents to take screenshots, move the mouse, click, and type on the keyboard across any operating system.

<details>
  <summary>Windows</summary>

  ##### AMD64

[AskUI Installer for AMD64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-AMD64-Web.exe)

##### ARM64

[AskUI Installer for ARM64](https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Win-ARM64-Web.exe)
</details>


<details>
  <summary>Linux</summary>

  **⚠️ Warning:** Agent OS currently does not work on Wayland. Switch to XOrg to use it.

##### AMD64

```shell
curl -L -o /tmp/AskUI-Suite-Latest-User-Installer-Linux-AMD64-Web.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Linux-AMD64-Web.run
```
```shell
bash /tmp/AskUI-Suite-Latest-User-Installer-Linux-AMD64-Web.run
```

##### ARM64


```shell
curl -L -o /tmp/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Web.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Web.run
```
```shell
bash /tmp/AskUI-Suite-Latest-User-Installer-Linux-ARM64-Web.run
```
</details>


<details>
  <summary>MacOS</summary>

```shell
curl -L -o /tmp/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Web.run https://files.askui.com/releases/Installer/Latest/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Web.run
```
```shell
bash /tmp/AskUI-Suite-Latest-User-Installer-MacOS-ARM64-Web.run
```
</details>


### 2. Install vision-agent in your Python environment

```shell
pip install askui
```

**Note:** Requires Python version >=3.10.

### 3a. Authenticate with an **AI Model** Provider

|  | AskUI [INFO](https://hub.askui.com/) | Anthropic [INFO](https://console.anthropic.com/settings/keys) |
|----------|----------|----------|
| ENV Variables    | `ASKUI_WORKSPACE_ID`, `ASKUI_TOKEN`   | `ANTHROPIC_API_KEY`   |
| Supported Commands    | `act()`, `click()`, `get()`, `locate()`, `mouse_move()`   | `act()`, `click()`, `get()`, `locate()`, `mouse_move()`  |
| Description    | Faster Inference, European Server, Enterprise Ready   | Supports complex actions   |

To get started, set the environment variables required to authenticate with your chosen model provider.

#### How to set an environment variable?
<details>
  <summary>Linux & MacOS</summary>

  Use export to set an evironment variable:

  ```shell
  export ASKUI_WORKSPACE_ID=<your-workspace-id-here>
  export ASKUI_TOKEN=<your-token-here>
  export ANTHROPIC_API_KEY=<your-api-key-here>
  ```
</details>

<details>
  <summary>Windows PowerShell</summary>

  Set an environment variable with $env:

  ```shell
  $env:ASKUI_WORKSPACE_ID="<your-workspace-id-here>"
  $env:ASKUI_TOKEN="<your-token-here>"
  $env:ANTHROPIC_API_KEY="<your-api-key-here>"
  ```
</details>


**Example Code:**
```python
from askui import VisionAgent

with VisionAgent() as agent:
    # AskUI used as default model

    agent.click("search field")

    # Use Anthropic (Claude 3.5 Sonnet V2) as model
    agent.click("search field", model="anthropic-claude-3-5-sonnet-20241022")
```


### 3b. Test with 🤗 Hugging Face **AI Models** (Spaces API)

You can test the Vision Agent with Huggingface models via their Spaces API. Please note that the API is rate-limited so for production use cases, it is recommended to choose step 3a.

**Note:** Hugging Face Spaces host model demos provided by individuals not associated with Hugging Face or AskUI. Don't use these models on screens with sensible information.

**Supported Models:**
- [`AskUI/PTA-1`](https://huggingface.co/spaces/AskUI/PTA-1)
- [`OS-Copilot/OS-Atlas-Base-7B`](https://huggingface.co/spaces/maxiw/OS-ATLAS)
- [`showlab/ShowUI-2B`](https://huggingface.co/spaces/showlab/ShowUI)
- [`Qwen/Qwen2-VL-2B-Instruct`](https://huggingface.co/spaces/maxiw/Qwen2-VL-Detection)
- [`Qwen/Qwen2-VL-7B-Instruct`](https://huggingface.co/spaces/maxiw/Qwen2-VL-Detection)

**Example Code:**
```python
    agent.click("search field", model="OS-Copilot/OS-Atlas-Base-7B")
```

### 3c. Host your own **AI Models**

#### UI-TARS

You can use Vision Agent with UI-TARS if you provide your own UI-TARS API endpoint.

1. Step: Host the model locally or in the cloud. More information about hosting UI-TARS can be found [here](https://github.com/bytedance/UI-TARS?tab=readme-ov-file#deployment).

2. Step: Provide the `TARS_URL` and `TARS_API_KEY` environment variables to Vision Agent.

3. Step: Use the `model="tars"` parameter in your `click()`, `get()` and `act()` etc. commands or when initializing the `VisionAgent`.


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

    # Or let the agent work on its own, needs an Anthropic key set
    agent.act("search for a flight from Berlin to Paris in January")
```

### 🎛️ Model Choice

You can choose different models for each `click()` (`act()`, `get()`, `locate()` etc.) command using the `model` parameter.

```python
from askui import VisionAgent

# Use AskUI's combo model for all commands
with VisionAgent(model="askui-combo") as agent:
    agent.click("Next")  # Uses askui-combo
    agent.get("What's on screen?")  # Uses askui-combo

# Use different models for different tasks
with VisionAgent(model={
    "act": "anthropic-claude-3-5-sonnet-20241022",  # Use Claude for act()
    "get": "askui",  # Use AskUI for get()
    "locate": "askui-combo",  # Use AskUI combo for locate() (and click(), mouse_move())
}) as agent:
    agent.act("Search for flights")  # Uses Claude
    agent.get("What's the current page?")  # Uses AskUI
    agent.click("Submit")  # Uses AskUI combo

# You can still override the default model for individual commands
with VisionAgent(model="askui-combo") as agent:
    agent.click("Next")  # Uses askui-combo (default)
    agent.click("Previous", model="askui-pta")  # Override with askui-pta
    agent.click("Submit")  # Back to askui-combo (default)
```

The following models are available:

<details>
  <summary>AskUI AI Models</summary>

Supported commands are: `act()`, `click()`, `get()`, `locate()`, `mouse_move()`
| Model Name  | Info | Execution Speed | Security | Cost | Reliability |
|-------------|--------------------|--------------|--------------|--------------|--------------|
| `askui` | `AskUI` is a combination of all the following models: `askui-pta`, `askui-ocr`, `askui-combo`, `askui-ai-element` where AskUI chooses the best model for the task depending on the input. | Fast, <500ms per step | Secure hosting by AskUI or on-premise | Low, <0,05$ per step | Recommended for production usage, can be (at least partially) retrained |
| `askui-pta` | [`PTA-1`](https://huggingface.co/AskUI/PTA-1) (Prompt-to-Automation) is a vision language model (VLM) trained by [AskUI](https://www.askui.com/) which to address all kinds of UI elements by a textual description e.g. "`Login button`", "`Text login`" | fast, <500ms per step | Secure hosting by AskUI or on-premise | Low, <0,05$ per step | Recommended for production usage, can be retrained |
| `askui-ocr` | `AskUI OCR` is an OCR model trained to address texts on UI Screens e.g. "`Login`", "`Search`" | Fast, <500ms per step | Secure hosting by AskUI or on-premise | low, <0,05$ per step | Recommended for production usage, can be retrained |
| `askui-combo` | AskUI Combo is an combination from the `askui-pta` and the `askui-ocr` model to improve the accuracy. | Fast, <500ms per step | Secure hosting by AskUI or on-premise | low, <0,05$ per step | Recommended for production usage, can be retrained |
| `askui-ai-element`| [AskUI AI Element](https://docs.askui.com/docs/general/Element%20Selection/aielement) allows you to address visual elements like icons or images by demonstrating what you looking for. Therefore, you have to crop out the element and give it a name.  | Very fast, <5ms per step | Secure hosting by AskUI or on-premise | Low, <0,05$ per step | Recommended for production usage, deterministic behaviour |

> **Note:** Configure your AskUI Model Provider [here](#3a-authenticate-with-an-ai-model-provider)

</details>

<details>
  <summary>Antrophic AI Models</summary>

Supported commands are: `act()`, `get()`, `click()`, `locate()`, `mouse_move()`
| Model Name  | Info | Execution Speed | Security | Cost | Reliability |
|-------------|--------------------|--------------|--------------|--------------|--------------|
| `anthropic-claude-3-5-sonnet-20241022` | The [Computer Use](https://docs.anthropic.com/en/docs/agents-and-tools/computer-use) model from Antrophic is a Large Action Model (LAM), which can autonomously achieve goals. e.g. `"Book me a flight from Berlin to Rom"` | slow, >1s per step | Model hosting by Anthropic | High, up to 1,5$ per act | Not recommended for production usage |
> **Note:** Configure your Antrophic Model Provider [here](#3a-authenticate-with-an-ai-model-provider)


</details>


<details>
  <summary>Huggingface AI Models (Spaces API)</summary>

Supported commands are: `click()`, `locate()`, `mouse_move()`
| Model Name  | Info | Execution Speed | Security | Cost | Reliability |
|-------------|--------------------|--------------|--------------|--------------|--------------|
| `AskUI/PTA-1` | [`PTA-1`](https://huggingface.co/AskUI/PTA-1) (Prompt-to-Automation) is a vision language model (VLM) trained by [AskUI](https://www.askui.com/) which to address all kinds of UI elements by a textual description e.g. "`Login button`", "`Text login`" | fast, <500ms per step | Huggingface hosted | Prices for Huggingface hosting | Not recommended for production applications |
| `OS-Copilot/OS-Atlas-Base-7B` | [`OS-Atlas-Base-7B`](https://github.com/OS-Copilot/OS-Atlas) is a Large Action Model (LAM), which can autonomously achieve goals. e.g. `"Please help me modify VS Code settings to hide all folders in the explorer view"`. This model is not available in the `act()` command | Slow, >1s per step | Huggingface hosted | Prices for Huggingface hosting | Not recommended for production applications |
| `showlab/ShowUI-2B` | [`showlab/ShowUI-2B`](https://huggingface.co/showlab/ShowUI-2B) is a Large Action Model (LAM), which can autonomously achieve goals. e.g. `"Search in google maps for Nahant"`. This model is not available in the `act()` command | slow, >1s per step | Huggingface hosted | Prices for Huggingface hosting | Not recommended for production usage |
| `Qwen/Qwen2-VL-2B-Instruct` | [`Qwen/Qwen2-VL-2B-Instruct`](https://github.com/QwenLM/Qwen2.5-VLB) is a Visual Language Model (VLM) pre-trained on multiple datasets including UI data. This model is not available in the `act()` command | slow, >1s per step | Huggingface hosted | Prices for Huggingface hosting | Not recommended for production usage |
| `Qwen/Qwen2-VL-7B-Instruct` | [Qwen/Qwen2-VL-7B-Instruct`](https://github.com/QwenLM/Qwen2.5-VLB) is a Visual Language Model (VLM) pre-trained on multiple dataset including UI data. This model is not available in the `act()` command available | slow, >1s per step | Huggingface hosted | Prices for Huggingface hosting | Not recommended for production usage |

> **Note:** No authentication required! But rate-limited!

</details>

<details>
  <summary>Self Hosted UI Models</summary>

Supported commands are: `act()`, `click()`, `get()`, `locate()`, `mouse_move()`
| Model Name  | Info | Execution Speed |  Security | Cost | Reliability |
|-------------|--------------------|--------------|--------------|--------------|--------------|
| `tars` | [`UI-Tars`](https://github.com/bytedance/UI-TARS) is a Large Action Model (LAM) based on Qwen2 and fine-tuned by [ByteDance](https://www.bytedance.com/) on UI data e.g. "`Book me a flight to rom`" | slow, >1s per step | Self-hosted | Depening on infrastructure | Out-of-the-box not recommended for production usage |


> **Note:** These models need to been self hosted by yourself. (See [here](#3c-host-your-own-ai-models))

</details>


### 🔧 Custom Models

You can create and use your own models by subclassing the `ActModel` (used for `act()`), `GetModel` (used for `get()`), or `LocateModel` (used for `click()`, `locate()`, `mouse_move()`) classes and registering them with the `VisionAgent`.

Here's how to create and use custom models:

```python
from askui import (
    ActModel,
    GetModel,
    LocateModel,
    Locator,
    ImageSource,
    ModelComposition,
    ModelRegistry,
    Point,
    ResponseSchema,
    VisionAgent,
)
from typing import Type

# Define custom models
class MyActModel(ActModel):
    def act(self, goal: str, model_choice: str) -> None:
        # Implement custom act logic, e.g.:
        # - Use a different AI model
        # - Implement custom business logic
        # - Call external services
        print(f"Custom act model executing goal: {goal}")

# Because Python supports multiple inheritance, we can subclass both `GetModel` and `LocateModel` (and even `ActModel`)
# to create a model that can both get and locate elements.
class MyGetAndLocateModel(GetModel, LocateModel):
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        # Implement custom get logic, e.g.:
        # - Use a different OCR service
        # - Implement custom text extraction
        # - Call external vision APIs
        return f"Custom response to query: {query}"


    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        # Implement custom locate logic, e.g.:
        # - Use a different object detection model
        # - Implement custom element finding
        # - Call external vision services
        return (100, 100)  # Example coordinates


# Create model registry
custom_models: ModelRegistry = {
    "my-act-model": MyActModel(),
    "my-get-model": MyGetAndLocateModel(),
    "my-locate-model": MyGetAndLocateModel(),
}

# Initialize agent with custom models
with VisionAgent(models=custom_models) as agent:
    # Use custom models for specific tasks
    agent.act("search for flights", model="my-act-model")

    # Get information using custom model
    result = agent.get(
        "what's the current page title?",
        model="my-get-model"
    )

    # Click using custom locate model
    agent.click("submit button", model="my-locate-model")

    # Mix and match with default models
    agent.click("next", model="askui")  # Uses default AskUI model
```

You can also use model factories if you need to create models dynamically:

```python
class DynamicActModel(ActModel):
    def act(self, goal: str, model_choice: str) -> None:
        # Use api_key in implementation
        pass


# going to be called each time model is chosen using `model` parameter
def create_custom_model(api_key: str) -> ActModel:
    return DynamicActModel()


# if you don't want to recreate a new model on each call but rather just initialize
# it lazily
@functools.cache
def create_custom_model_cached(api_key: str) -> ActModel:
    return DynamicActModel()


# Register model factory
custom_models: ModelRegistry = {
    "dynamic-model": lambda: create_custom_model("your-api-key"),
    "dynamic-model-cached": lambda: create_custom_model_cached("your-api-key"),
    "askui": lambda: create_custom_model_cached("your-api-key"), # overrides default model
    "anthropic-claude-3-5-sonnet-20241022": lambda: create_custom_model_cached("your-api-key"), # overrides model
}


with VisionAgent(models=custom_models, model="dynamic-model") as agent:
    agent.act("do something") # creates and uses instance of DynamicActModel
    agent.act("do something") # creates and uses instance of DynamicActModel
    agent.act("do something", model="dynamic-model-cached") # uses new instance of DynamicActModel as it is the first call
    agent.act("do something", model="dynamic-model-cached") # reuses cached instance
```


### 🛠️ Direct Tool Use

Under the hood, agents are using a set of tools. You can directly access these tools.

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

### 📜 Reporting

You want to see a report of the actions your agent took? Register a reporter using the `reporters` parameter.

```python
from typing import Optional, Union
from typing_extensions import override
from askui.reporting import SimpleHtmlReporter
from PIL import Image

with VisionAgent(reporters=[SimpleHtmlReporter()]) as agent:
    agent...
```

You can also create your own reporter by implementing the `Reporter` interface.

```python
from askui.reporting import Reporter

class CustomReporter(Reporter):
    @override
    def add_message(
        self,
        role: str,
        content: Union[str, dict, list],
        image: Optional[Image.Image | list[Image.Image]] = None,
    ) -> None:
        # adding message to the report (see implementation of `SimpleHtmlReporter` as an example)
        pass

    @override
    def generate(self) -> None:
        # generate the report if not generated live (see implementation of `SimpleHtmlReporter` as an example)
        pass


with VisionAgent(reporters=[CustomReporter()]) as agent:
    agent...
```

You can also use multiple reporters at once. Their `generate()` and `add_message()` methods will be called in the order of the reporters in the list.

```python
with VisionAgent(reporters=[SimpleHtmlReporter(), CustomReporter()]) as agent:
    agent...
```

### 🖥️ Multi-Monitor Support

You have multiple monitors? Choose which one to automate by setting `display` to `1`, `2` etc. To find the correct display or monitor, you have to play play around a bit setting it to different values. We are going to improve this soon. By default, the agent will use display 1.

```python
with VisionAgent(display=1) as agent:
    agent...
```

### 🎯 Locating elements

If you have a hard time locating (clicking, moving mouse to etc.) elements by simply using text, e.g.,

```python
agent.click("Password textfield")
agent.type("********")
```

you can build more sophisticated locators.

**⚠️ Warning:** Support can vary depending on the model you are using. Currently, only, the `askui` model provides best support for locators. This model is chosen by default if `ASKUI_WORKSPACE_ID` and `ASKUI_TOKEN` environment variables are set and it is not overridden using the  `model` parameter.

Example:

```python
from askui import locators as loc

password_textfield_label = loc.Text("Password")
password_textfield = loc.Element("textfield").right_of(password_textfield_label)

agent.click(password_textfield)
agent.type("********")
```

### 📊 Extracting information

The `get()` method allows you to extract information from the screen. You can use it to:

- Get text or data from the screen
- Check the state of UI elements
- Make decisions based on screen content
- Analyze static images

#### Basic usage

```python
# Get text from screen
url = agent.get("What is the current url shown in the url bar?")
print(url)  # e.g., "github.com/login"

# Check UI state
# Just as an example, may be flaky if used as is, better use a response schema to check for a boolean value (see below)
is_logged_in = agent.get("Is the user logged in? Answer with 'yes' or 'no'.") == "yes"
if is_logged_in:
    agent.click("Logout")
else:
    agent.click("Login")
```

#### Using custom images

Instead of taking a screenshot, you can analyze specific images:

```python
from PIL import Image
from askui import VisionAgent

# From PIL Image
with VisionAgent() as agent:
  image = Image.open("screenshot.png")
  result = agent.get("What's in this image?", image)

  # From file path
  result = agent.get("What's in this image?", "screenshot.png")
```

#### Using response schemas

For structured data extraction, use Pydantic models extending `ResponseSchemaBase`:

```python
from askui import ResponseSchemaBase

class UserInfo(ResponseSchemaBase):
    username: str
    is_online: bool

# Get structured data
user_info = agent.get(
    "What is the username and online status?",
    response_schema=UserInfo
)
print(f"User {user_info.username} is {'online' if user_info.is_online else 'offline'}")
```

**⚠️ Limitations:**
- Nested Pydantic schemas are not currently supported
- Response schema is currently only supported by "askui" model (default model if `ASKUI_WORKSPACE_ID` and `ASKUI_TOKEN` are set)

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


## Telemetry

By default, we record usage data to detect and fix bugs inside the package and improve the UX of the package including
- version of the `askui` package used
- information about the environment, e.g., operating system, architecture, device id (hashed to protect privacy), python version
- session id
- some of the methods called including (non-sensitive) method parameters and responses, e.g., the click coordinates in `click(x=100, y=100)`
- exceptions (types and messages)
- AskUI workspace and user id if `ASKUI_WORKSPACE_ID` and `ASKUI_TOKEN` are set

If you would like to disable the recording of usage data, set the `ASKUI__VA__TELEMETRY__ENABLED` environment variable to `False`.


## Experimental Features

### Chat

The chat is a streamlit app that allows you to give an agent instructions and observe via messages by the agent given as a response the reasoning and actions taken by the action in return. The actions can be replayed afterwards.

Instead of giving an agent instructions about what to do, it also allows demonstrating/simulating certain actions (left clicking, typing, mouse moving) directly and replay those actions.

Configure the chat by setting the following environment variables:

- `ANTHROPIC_API_KEY`
- `ASKUI_WORKSPACE_ID`
- `ASKUI_TOKEN`

Start the chat with:

```bash
pdm run chat
```

This should open the streamlit app in your default browser.

Currently, the chat is in the experimental stage and has a lot of issues, for example:

- You cannot cancel/stop the agent while it is running except by terminating/killing streamlit or hitting "stop" within the streamlit app.
- There is no option to retry a failed prompt.
- A chat/thread cannot be deleted.
- The agent often responds with that it cannot solve an issue because it does not see what to do.
- No option to edit message in a thread or start a new thread from an existing thread by editing a message within it or retrying a certain message.
- You have to rerun all actions taken by the agent even though they may have not lead to the goal and are, in fact, redundant.
- Often the agent does not get which window has focus --> You can tell it in the prompt and tell it to click on the window to interact with first to make sure it has focus.
- Often the agent goes into crazy loops.
- Display id cannot be configured but instead display 1 is taken by default.
- Connection issues with controller, e.g., if there are multiple chat sessions open at the same time, or if the agent was killed/terminated --> Restart controller, restart streamlit app, make sure it is the only controller and streamlit app session running.
- The chat sessions are identified by timestamp of when they were created.
