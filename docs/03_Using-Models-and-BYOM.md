# Using Models and BYOM (Bring Your Own Model)

AskUI Vision Agent uses three **provider slots** — one per AI capability. You configure the agent once via `AgentSettings`; the same providers power both the agentic loop (`act()`) and the direct commands (`get()`, `locate()`).

## Provider Slots

| Slot | Used by | Default |
|------|---------|---------|
| `vlm_provider` | `act()` — multimodal input + tool-calling | `AskUIVlmProvider` |
| `image_qa_provider` | `get()` — Q&A and structured extraction | `AskUIImageQAProvider` |
| `detection_provider` | `locate()`, `click()`, etc. — element coordinates | `AskUIDetectionProvider` |

Credentials are read from environment variables and validated **lazily** — only on the first API call.

---

## Default Setup

No configuration required. Credentials are read from `ASKUI_WORKSPACE_ID` and `ASKUI_TOKEN`:

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    agent.act("Open the calculator")
    result = agent.get("What is shown on the display?")
    agent.click("Clear button")
```

---

## Configuring Model IDs

Override the model ID for any AskUI-hosted provider:

```python
from askui import AgentSettings, ComputerAgent
from askui.model_providers import AskUIVlmProvider, AskUIImageQAProvider

with ComputerAgent(settings=AgentSettings(
    vlm_provider=AskUIVlmProvider(model_id="claude-opus-4-5-20251101"),
    image_qa_provider=AskUIImageQAProvider(model_id="gemini-2.5-pro"),
)) as agent:
    agent.act("Complete the checkout process")
```

**Available AskUI providers:**

| Class | Default model |
|-------|--------------|
| `AskUIVlmProvider` | `claude-sonnet-4-5-20251101` |
| `AskUIImageQAProvider` | `gemini-2.5-flash` |
| `AskUIDetectionProvider` | — (no model ID) |

---

## Using Anthropic Directly

Use your own Anthropic API key instead of the AskUI proxy:

```python
import os
from askui import AgentSettings, ComputerAgent
from askui.model_providers import AnthropicVlmProvider, AnthropicImageQAProvider

with ComputerAgent(settings=AgentSettings(
    vlm_provider=AnthropicVlmProvider(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model_id="claude-sonnet-4-5-20251101",
    ),
    image_qa_provider=AnthropicImageQAProvider(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model_id="claude-haiku-4-5-20251101",
    ),
)) as agent:
    agent.act("Navigate to the settings page")
    value = agent.get("What is the current theme?")
```

You can omit `api_key` and set `ANTHROPIC_API_KEY` in the environment instead — it is read lazily on first use.

---

## Mixing Providers

Each slot is independent. Mix and match freely:

```python
from askui import AgentSettings, ComputerAgent
from askui.model_providers import (
    AnthropicVlmProvider,
    GoogleImageQAProvider,
    AskUIDetectionProvider,
)

with ComputerAgent(settings=AgentSettings(
    vlm_provider=AnthropicVlmProvider(model_id="claude-opus-4-5-20251101"),
    image_qa_provider=GoogleImageQAProvider(api_key="...", model_id="gemini-2.5-flash"),
    detection_provider=AskUIDetectionProvider(),          # AskUI for element detection
)) as agent:
    agent.act("Find the cheapest item and add it to cart")
```

---

## BYOM: OpenAI-Compatible Endpoint

Point `vlm_provider` at any OpenAI-compatible chat completions endpoint:

```python
from askui import AgentSettings, ComputerAgent
from askui.model_providers import OpenAICompatibleProvider

with ComputerAgent(settings=AgentSettings(
    vlm_provider=OpenAICompatibleProvider(
        endpoint="http://localhost:11434/v1/chat/completions",
        api_key="none",   # required field; use any value for unauthenticated endpoints
        model_id="llama3.2",
    ),
)) as agent:
    agent.act("Summarize what is on the screen")
```

---

## BYOM: Custom Provider

Implement any of the three provider interfaces:

```python
from typing import Type
from typing_extensions import override
from askui import AgentSettings, ComputerAgent
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
        # call your own API here
        return "my answer"


with ComputerAgent(settings=AgentSettings(
    image_qa_provider=MyImageQAProvider(),
)) as agent:
    result = agent.get("What is the page title?")
    print(result)
```

The three interfaces to implement:

| Interface | Method to implement | Used by |
|-----------|--------------------|---------|
| `VlmProvider` | `create_message(messages, tools, ...)` | `act()` |
| `ImageQAProvider` | `query(query, source, response_schema, get_settings)` | `get()` |
| `DetectionProvider` | `detect(locator, image, locate_settings)` | `locate()`, `click()` |

---

## Model Settings

Fine-tune model behaviour through settings classes. Settings can be passed per call or configured on the agent:

```python
from askui import ComputerAgent
from askui.models.shared.settings import ActSettings, GetSettings, MessageSettings

with ComputerAgent() as agent:
    # Per-call act settings
    agent.act(
        "Complete the form",
        act_settings=ActSettings(
            messages=MessageSettings(max_tokens=16384, temperature=0.5)
        ),
    )

    # Per-call get settings
    result = agent.get(
        "Extract the table",
        get_settings=GetSettings(max_tokens=4096),
    )
```
