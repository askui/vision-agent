# Using Models and BYOM (Bring Your Own Model)

AskUI Vision Agent uses three **provider slots** — one per AI capability. Configure them via `AgentSettings`; the same providers power both the agentic loop (`act()`) and direct commands (`get()`, `locate()`).

## Provider Slots

| Slot | Used by | Default |
|------|---------|---------|
| `vlm_provider` | `act()` — multimodal input + tool-calling | `AskUIVlmProvider` |
| `image_qa_provider` | `get()` — Q&A and structured extraction | `AskUIImageQAProvider` |
| `detection_provider` | `locate()`, `click()`, etc. — element coordinates | `AskUIDetectionProvider` |

Credentials are read from environment variables and validated **lazily** — only on the first API call.

---

## Architecture

Providers follow a layered architecture:

```
Provider → Model → MessagesAPI → Client
```

- **Provider**: User-facing configuration layer (`AskUIVlmProvider`, `AnthropicVlmProvider`, etc.)
- **Model**: Internal implementation handling the agent loop (e.g., `AnthropicActModel`)
- **MessagesAPI**: Converts internal message format to provider-specific format
- **Client**: Underlying HTTP client (`Anthropic`, `OpenAI`, etc.)

Users typically configure only the **Provider**. For advanced use cases, you can inject a pre-configured **Client**.

---

## Default Setup

No configuration required. Set `ASKUI_WORKSPACE_ID` and `ASKUI_TOKEN` in your environment:

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    agent.act("Open the calculator")
    result = agent.get("What is shown on the display?")
```

---

## Configuring Model IDs

Override the model for any provider:

```python
from askui import AgentSettings, ComputerAgent
from askui.model_providers import AskUIVlmProvider, AskUIImageQAProvider

with ComputerAgent(settings=AgentSettings(
    vlm_provider=AskUIVlmProvider(model_id="claude-opus-4-5-20251101"),
    image_qa_provider=AskUIImageQAProvider(model_id="gemini-2.5-pro"),
)) as agent:
    agent.act("Complete the checkout process")
```

---

## Using Anthropic Directly

Use your own Anthropic API key:

```python
import os
from askui import AgentSettings, ComputerAgent
from askui.model_providers import AnthropicVlmProvider

with ComputerAgent(settings=AgentSettings(
    vlm_provider=AnthropicVlmProvider(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model_id="claude-sonnet-4-5-20251101",
    ),
)) as agent:
    agent.act("Navigate to settings")
```

---

## Advanced: Injecting a Custom Client

For full control over HTTP settings (timeouts, proxies, retries), inject a pre-configured client:

```python
import os
from anthropic import Anthropic
from askui import AgentSettings, ComputerAgent
from askui.model_providers import AnthropicVlmProvider

client = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    timeout=60.0,
    max_retries=3,
)

with ComputerAgent(settings=AgentSettings(
    vlm_provider=AnthropicVlmProvider(client=client),
)) as agent:
    agent.act("Process the document")
```

---

## BYOM: Custom Provider

Implement one of the three provider interfaces:

```python
from typing import Type
from typing_extensions import override
from askui.model_providers import ImageQAProvider
from askui.models.shared.settings import GetSettings
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.source_utils import Source


class MyImageQAProvider(ImageQAProvider):
    @property
    def model_id(self) -> str:
        return "my-model-v1"

    @override
    def query(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        get_settings: GetSettings,
    ) -> ResponseSchema | str:
        return "my answer"  # call your API here
```

| Interface | Method | Used by |
|-----------|--------|---------|
| `VlmProvider` | `create_message(...)` | `act()` |
| `ImageQAProvider` | `query(...)` | `get()` |
| `DetectionProvider` | `detect(...)` | `locate()`, `click()` |

---

## Model Settings

Fine-tune model behaviour per call:

```python
from askui import ComputerAgent
from askui.models.shared.settings import ActSettings, GetSettings, MessageSettings

with ComputerAgent() as agent:
    agent.act(
        "Complete the form",
        act_settings=ActSettings(messages=MessageSettings(max_tokens=16384)),
    )
    result = agent.get("Extract the table", get_settings=GetSettings(max_tokens=4096))
```

---

## Provider-Specific Options

`MessageSettings` includes a `provider_options` field for passing provider-specific configuration that doesn't fit into the standard parameters.

This is a `dict[str, Any]` where keys and values depend on the provider being used. Common use cases include:

- **Beta features**: Enabling experimental provider features (e.g., `{"betas": ["feature-name"]}` for Anthropic)
- **Provider extensions**: Passing custom headers, metadata, or other provider-specific parameters

Use `provider_options` when you need to access functionality that is specific to a particular provider and not abstracted by the standard `MessageSettings` fields. Most users will not need this — it is intended for advanced use cases where provider-specific behaviour is required.
