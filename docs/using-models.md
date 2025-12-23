# Using Models

This guide covers all the AI models available in AskUI Vision Agent, their capabilities, how to authenticate with them, and how to create custom models. AskUI Vision Agent supports multiple AI model providers and self-hosted models, each with different strengths and use cases.

**Important Note:** Although we would love to support all kinds of models, models hosted by us (AskUI) are our primary focus and receive the most comprehensive support, testing, and optimization. Other models rely on community contributions and may have varying levels of support. We highly appreciate community contributions to improve support for other models!

## Table of Contents

- [When to select a different model](#when-to-select-a-different-model)
- [How to select a model](#how-to-select-a-model)
- [AskUI models](#askui-models)
- [Other models and providers: Anthropic, OpenRouter, Huggingface, UI-TARS](#other-models-and-providers-anthropic-openrouter-huggingface-ui-tars)
- [Your own custom models](#your-own-custom-models)
- [Model providers](#model-providers)

## When to select a different model

The default model is `askui` which is a combination of all kinds of models hosted by us that we selected based on our experience, testing and benchmarking to give you the best possible experience. All those models are hosted in Europe and are enterprise ready.

But there are cases where you might want to have more control and rather
- use a specific AskUI-hosted model,
- try out a new model released by another provider, e.g., Anthropic, OpenRouter, Huggingface, UI-TARS, etc. or
- use your own model.

## How to select a model

You can choose different models for each command using the `model` parameter:

```python
from askui import VisionAgent

# Use AskUI's combo model for all commands
with VisionAgent(model="askui-combo") as agent:
    agent.click("Next")  # Uses askui-combo
    agent.get("What's on screen?")  # Uses askui-combo

# Use different models for different tasks (more about that later)
with VisionAgent(model={
    "act": "claude-sonnet-4-20250514",  # Use Claude for act()
    "get": "askui",  # Use AskUI for get()
    "locate": "askui-combo",  # Use AskUI combo for locate() (and click(), mouse_move() etc.)
}) as agent:
    agent.act("Search for flights")  # Uses Claude
    agent.get("What's the current page?")  # Uses AskUI
    agent.click("Submit")  # Uses AskUI combo

# Override the default model for individual commands
with VisionAgent(model="askui-combo") as agent:
    agent.click("Next")  # Uses askui-combo (default)
    agent.click("Previous", model="askui-pta")  # Override with askui-pta
    agent.click("Submit")  # Back to askui-combo (default)
```

**Recommendation:** Start with the default model (`askui`) as we can automatically choose the best model for each task. Only specify a specific model when you need particular capabilities or have specific requirements.

## AskUI models

### Model Cards

| Model Name | Strengths | Execution Speed | Reliability |
|------------|-----------|----------------|-------------|
| `askui` | **Best overall choice** - Automatically selects optimal model for each task. Combines all AskUI models intelligently. | Fast, <500ms per step, but highly dependent on the task, e.g., `act()` is going to be slow (as it is multip-step) while `get()` or `click()` is going to be faster | **Highest** - Recommended for production usage |
| `askui-pta` | Excellent for UI element identification by description (e.g., "Login button", "Text login"), only supported for `click()`, `locate()`, `mouse_move()` etc. | Fast, <500ms per step | **High** - Can be retrained |
| `askui-ocr` | Specialized for text recognition on UI screens (e.g., "Login", "Search"), only supported for `click()`, `locate()`, `mouse_move()` etc. | Fast, <500ms per step | **High** - Can be retrained |
| `askui-combo` | Combines PTA and OCR for improved accuracy, only supported for `click()`, `locate()`, `mouse_move()` etc. | Fast, <500ms per step | **High** - Can be retrained |
| `askui-ai-element` | Very fast for visual element matching (icons, images) using demonstrations, only supported for `click()`, `locate()`, `mouse_move()` etc. | Very fast, <5ms per step | **High** - Deterministic behavior |
| `askui/gemini-2.5-flash` | Excellent for asking questions about screenshots/images, only supported for `get()` | Fast, <500ms per extraction | **Low** |
| `askui/gemini-2.5-pro` | Best quality responses for complex image analysis, only supported for `get()` | Slow, ~1s per extraction | **High** |

### Configuration

**Environment Variables:**
```shell
export ASKUI_WORKSPACE_ID=<your-workspace-id-here>
export ASKUI_TOKEN=<your-token-here>
```

## Other models and providers: Anthropic, OpenRouter, Huggingface, UI-TARS

**Note:** These models rely on community support and may have varying levels of integration. We welcome and appreciate community contributions to improve their support!

### Anthropic

#### Model Card

| Model Name | Strengths | Execution Speed | Reliability |
|------------|-----------|----------------|-------------|
| `claude-sonnet-4-20250514` | Excellent for autonomous goal achievement and complex reasoning tasks | Slow, >1s per step | **Medium** - stable |
| `claude-haiku-4-5-20251001` | Excellent for autonomous goal achievement and complex reasoning tasks | Fast, <1s per step | **Medium** - stable |
| `claude-sonnet-4-5-20250929` | Excellent for autonomous goal achievement and complex reasoning tasks | Slow, >1s per step | **High** - stable |
| `claude-opus-4-5-20251101` | Excellent for autonomous goal achievement and complex reasoning tasks | Slow, >1s per step | **High** - stable |

#### Configuration

**Environment Variables:**
```shell
export ANTHROPIC_API_KEY=<your-api-key-here>
```

### OpenRouter

**Supported commands:** `get()`

#### Model Card

| Model Name | Strengths | Execution Speed | Reliability |
|------------|-----------|----------------|-------------|
| Various models via OpenRouter | Access to wide variety of models through unified API | Varies by model | **Medium** - Depends on underlying model |

#### Configuration

**Environment Variables:**
```shell
export OPEN_ROUTER_API_KEY=<your-openrouter-api-key>
export OPEN_ROUTER_MODEL=<your-model-name>  # Optional, defaults to "openrouter/auto"
export OPEN_ROUTER_BASE_URL=<your-base-url>  # Optional, defaults to "https://openrouter.ai/api/v1"
```

**Note:** OpenRouter integration requires passing a custom GetModel instance to the `get()` method. See the [custom models](#your-own-custom-models) section for examples.

### Huggingface AI Models (Spaces API)

**Supported commands:** All but `act()` and `get()` command

#### Model Cards

| Model Name | Strengths | Execution Speed | Reliability |
|------------|-----------|----------------|-------------|
| `AskUI/PTA-1` | Same as askui-pta but via Huggingface | Fast, <500ms per step | **Low** - depends on UI |
| `OS-Copilot/OS-Atlas-Base-7B` | Good for autonomous goal achievement | - | **Low** - Not recommended for production |
| `showlab/ShowUI-2B` | Good for autonomous goal achievement | - | **Low** - Not recommended for production |
| `Qwen/Qwen2-VL-2B-Instruct` | Good for visual language tasks | - | **Low** - Not recommended for production |
| `Qwen/Qwen2-VL-7B-Instruct` | Better quality than 2B version | - | **Low** - Not recommended for production |

#### Configuration

**No authentication required** - but rate-limited!

**Example Usage:**
```python
from askui import VisionAgent

with VisionAgent() as agent:
    agent.click("search field", model="OS-Copilot/OS-Atlas-Base-7B")
```

**Note:** Hugging Face Spaces host model demos provided by individuals not associated with Hugging Face or AskUI. Don't use these models on screens with sensitive information.

### UI-TARS

You need to host UI-TARS yourself. More information about hosting can be found [here](https://github.com/bytedance/UI-TARS).

#### Model Card

| Model Name | Strengths | Execution Speed | Reliability |
|------------|-----------|----------------|-------------|
| `tars` | Good for autonomous goal achievement | Slow, >1s per step | **Medium** - Out-of-the-box not recommended for production |

#### Configuration

**Environment Variables:**
```shell
export TARS_URL=<your-tars-endpoint>
export TARS_API_KEY=<your-tars-api-key>
export TARS_MODEL_NAME=<your-model-name>
```

**Example Usage:**
```python
from askui import VisionAgent

with VisionAgent(model="tars") as agent:
    agent.click("Submit button")  # Uses TARS automatically
    agent.get("What's on screen?")  # Uses TARS automatically
    agent.act("Search for flights")  # Uses TARS automatically
```

**Note:** You need to host UI-TARS yourself. More information about hosting can be found [here](https://github.com/bytedance/UI-TARS?tab=readme-ov-file#deployment).

## Your own custom models

For `get()` and `locate()` operations, you can provide custom model implementations by passing them directly to the methods. This is useful when you need to:

- Integrate external vision APIs
- Implement custom OCR or element detection logic
- Add custom business logic or validation
- Use models not natively supported by AskUI

### Custom GetModel

You can create a custom model for extracting information from images:

```python
from askui import GetModel, VisionAgent, ResponseSchema
from askui.utils.source_utils import Source
from typing import Type
from typing_extensions import override

class MyGetModel(GetModel):
    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        model: str,
    ) -> ResponseSchema | str:
        # Implement your custom logic here
        # For example: call external API, apply custom processing, etc.
        return f"Custom response to: {query}"

# Use the custom model
with VisionAgent() as agent:
    custom_model = MyGetModel()
    result = agent.get("What's on screen?", get_model=custom_model)
```

### Custom LocateModel

You can create a custom model for locating UI elements:

```python
from askui import LocateModel, VisionAgent, PointList
from askui.locators.locators import Locator
from askui.utils.image_utils import ImageSource
from askui.models import ModelComposition
from typing_extensions import override

class MyLocateModel(LocateModel):
    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model: ModelComposition | str,
    ) -> PointList:
        # Implement your custom element detection logic
        # For example: use custom vision API, apply custom algorithms, etc.
        return [(100, 100)]  # Return coordinates

# Use the custom model
with VisionAgent() as agent:
    custom_model = MyLocateModel()
    point = agent.locate("Submit button", locate_model=custom_model)
```

### For act() operations

For `act()` operations, use the available model providers (Anthropic, AskUI, Bedrock, Vertex) via the `model` parameter. Custom act implementations are not currently supported.

If you need enterprise-level custom model integration, please contact AskUI support.

## Model providers

### Using a model provider

You can configure the model provider by setting the `ASKUI__VA__MODEL_PROVIDER` environment variable, e.g., `"bedrock"` to use Bedrock models. All the models you pass via `model` parameter of `act()`, `get()`, `locate()` will be prefixed with `"bedrock/"` in this case, e.g., if you call `agent.act("do something", model="anthropic.claude-sonnet-4-20250514-v1:0")`, it will be called as `agent.act("do something", model="bedrock/anthropic.claude-sonnet-4-20250514-v1:0")` under the hood. Alternatively, just prefix the model name(s) you pass via `model` parameter, e.g., `agent.act("do something", model="bedrock/anthropic.claude-sonnet-4-20250514-v1:0")` or `agent.act("do something", model="vertex/claude-sonnet-4@20250514")`.

At the time of writing, the following model providers are available:
- `"bedrock"`: Use models hosted on AWS Bedrock.
- `"vertex"`: Use models hosted on Google Vertex AI.
- `"anthropic"`: Use models hosted behind Anthropic API.
- `"askui"`: Use models hosted behind AskUI API.

**IMPORTANT:** If you pass a `model` argument at construction, this is not going to be prefixed with the model provider, e.g., if you call `VisionAgent(model="claude-sonnet-4-20250514", model_provider="askui")`, and later call `agent.act("do something")`, it will be called as `agent.act("do something", model="claude-sonnet-4-20250514")` and not as `agent.act("do something", model="askui/claude-sonnet-4-20250514")` under the hood. If you want to use a provider per default, just prefix the model name(s) you pass via `model` parameter, e.g., `VisionAgent(model="askui/claude-sonnet-4-20250514")` or `VisionAgent(model={"act": "askui/claude-sonnet-4-20250514"})`.

You can also set the `model` parameter of an agent via environment variable, e.g., `ASKUI__VA__MODEL`. For complex values, just use json, e.g., `ASKUI__VA__MODEL={"act":"askui/claude-sonnet-4-20250514"}`.

**IMPORTANT:** Keep in mind that the model name may differ between providers and not all providers may support a model (see https://docs.claude.com/en/docs/about-claude/models/overview). `askui` uses the same model names as `anthropic`. For `vertex` see https://docs.claude.com/en/api/claude-on-vertex-ai and for `bedrock` see https://docs.claude.com/en/api/claude-on-amazon-bedrock.

**IMPORTANT:** Keep in mind that when using a custom model that you may have to pass different `settings` to act as the settings support, e.g., tool or betas, differs between models, e.g., `agent.act("do something", model="askui/<a-special-model>", settings=ActSettings(tools=[ASpecialTool()]))`.

### Configure provider

The following environment variables control authentication and behavior per provider. Variables marked as required must be set for that provider, unless your environment provides credentials through instance/role bindings or local SDK configuration.

#### Common
- `ASKUI__VA__MODEL_PROVIDER` (str, optional): Provider prefix to apply automatically (e.g., `bedrock`, `vertex`, `anthropic`, `askui`). Per default, no provider prefix is applied, e.g., `claude-sonnet-4-20250514` is going to be called as `claude-sonnet-4-20250514` and not as `bedrock/claude-sonnet-4-20250514` under the hood.
- `ASKUI__VA__MODEL` (str | json): Default model or per-capability map. Example: `{"act":"bedrock/claude-sonnet-4-20250514"}`.

#### `askui` provider
- `ASKUI_WORKSPACE_ID` (UUID, required): Workspace to route requests to.
- `ASKUI_TOKEN` (str) or `ASKUI__AUTHORIZATION` (str): Exactly one required. If `ASKUI__AUTHORIZATION` is set, it is used verbatim as the `Authorization` header. Takes precedence over `ASKUI_TOKEN`.
- `ASKUI_INFERENCE_ENDPOINT` (url, optional): Override base endpoint. Default: `https://inference.askui.com`.

#### `anthropic` provider (see https://docs.claude.com/en/docs/get-started#python)
- `ANTHROPIC_API_KEY` (str, required): Anthropic API key.
- `ANTHROPIC_AUTH_TOKEN` (str, optional): Anthropic auth token.
- `ANTHROPIC_BASE_URL` (url, optional): Base URL to use for Anthropic API.

#### `bedrock` provider (via Anthropic Bedrock client, see https://docs.claude.com/en/api/claude-on-bedrock)
- Uses standard AWS credential resolution. Set one of:
- `AWS_PROFILE` (str) or static credentials `AWS_ACCESS_KEY_ID` (str), `AWS_SECRET_ACCESS_KEY` (str), optional `AWS_SESSION_TOKEN` (str).
- Region (required): `AWS_REGION` (str) or `AWS_DEFAULT_REGION` (str).
- Any other AWS SDK configuration is respected (env, shared config/credentials files, instance role, SSO, etc.).
- `ANTHROPIC_BEDROCK_BASE_URL` (url, optional): Base URL to use for Bedrock API.

#### `vertex` provider (via Anthropic Vertex client, see https://docs.claude.com/en/api/claude-on-vertex-ai)
- Uses Google Application Default Credentials (ADC). Common setups:
    - `GOOGLE_APPLICATION_CREDENTIALS` (path): Service account JSON key file.
    - Or gcloud-authenticated user with `gcloud auth application-default login`.
    - Project and location are resolved from ADC and/or environment; typical envs if needed in your setup: `GOOGLE_CLOUD_PROJECT` (str), `GOOGLE_CLOUD_LOCATION` (str). Consult your org’s Vertex configuration if these are required.
- `CLOUD_ML_REGION` (str): Region to use for Vertex AI.
- `ANTHROPIC_VERTEX_BASE_URL` (url): Base URL to use for Vertex AI.
- `ANTHROPIC_VERTEX_PROJECT_ID` (str): Project ID to use for Vertex AI.

```python
import os

from askui import VisionAgent

os.environ["ANTHROPIC_VERTEX_PROJECT_ID"] = "test-project"
os.environ["CLOUD_ML_REGION"] = "europe-west1"

with VisionAgent() as agent:
    agent.act("do something", model="vertex/claude-sonnet-4@20250514")

# or

with VisionAgent(model_provider="vertex") as agent:
    agent.act("do something", model="claude-sonnet-4@20250514")

# or

with VisionAgent(model="vertex/claude-sonnet-4@20250514") as agent:
    agent.act("do something")

# or

os.environ["ASKUI__VA__MODEL"] = '{"act":"vertex/claude-sonnet-4@20250514"}'
with VisionAgent() as agent:
    agent.act("do something")
```
