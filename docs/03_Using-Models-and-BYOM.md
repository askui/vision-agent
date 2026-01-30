# Using Models and BYOM (Bring Your Own Model)

This guide covers the AI model system in AskUI Vision Agent, including how to use built-in models, configure model settings, and create custom models.

## Table of Contents

- [Understanding the Three Model Types](#understanding-the-three-model-types)
- [Available Models](#available-models)
- [Using Default Models](#using-default-models)
- [Specifying Models at Construction](#specifying-models-at-construction)
- [Per-Call Model Overrides](#per-call-model-overrides)
- [Model Settings](#model-settings)
- [BYOM: Bring Your Own Model](#byom-bring-your-own-model)
- [Best Practices](#best-practices)

## Understanding the Three Model Types

AskUI Vision Agent uses three distinct types of AI models, each specialized for different tasks:

### ActModel
Used by the `agent.act()` method for autonomous goal achievement. ActModels can:
- Execute multi-step workflows
- Make decisions about which actions to take
- Use tools (clicking, typing, scrolling, etc.)
- Achieve complex goals through reasoning

**When it's used:** Every time you call `agent.act("do something")`

### GetModel
Used by the `agent.get()` method for information extraction. GetModels can:
- Answer questions about screenshots or images
- Extract structured data from visual content
- Analyze PDFs and documents
- Return responses as strings or Pydantic models

**When it's used:** Every time you call `agent.get("what's on screen?")`

### LocateModel
Used by `agent.click()`, `agent.locate()`, `agent.locate_all()`, and `agent.mouse_move()` to find UI elements. LocateModels can:
- Find elements by text description
- Locate elements by visual appearance
- Return coordinates of UI elements
- Support various locator types (text, image, prompt, etc.)

**When it's used:** Every time you call `agent.click("button")`, `agent.locate("field")`, etc.

## Available Models

### Model Store

The `askui.model_store` module provides factory functions for creating model instances:

```python
from askui.model_store import (
    create_askui_act_model,     # Default act model (Claude Sonnet 4 via AskUI)
    create_askui_get_model,     # Default get model (Gemini 2.5 Flash + AskUI)
    create_askui_locate_model,  # Default locate model (AskUI vision models)
)
```

### Available Factory Functions

| Factory Function | Model Type | Example |
|-----------------|------------|----------|
| `create_askui_act_model()` | ActModel | Claude Sonnet 4 via AskUI for autonomous actions |
| `create_askui_get_model()` | GetModel | Gemini 2.5 Flash for information extraction |
| `create_askui_locate_model()` | LocateModel | AskUI vision models for element location |

### Model Discovery

You can discover available models programmatically:

```python
from askui import model_store

# List all available models
models = model_store.list_available_models()

for name, metadata in models.items():
    print(f"{name}:")
    print(f"  Type: {metadata['type']}")
    print(f"  Provider: {metadata['provider']}")
    print(f"  Description: {metadata['description']}")

# Output:
# askui_act:
#   Type: act
#   Provider: askui
#   Description: AskUI default agentic model (Claude Sonnet 4 via AskUI)
# askui_get:
#   Type: get
#   Provider: askui
#   Description: AskUI default info extraction (Gemini 2.5 Flash + AskUI)
# askui_locate:
#   Type: locate
#   Provider: askui
#   Description: AskUI default element locator (AskUI vision models)

# Create a model from the registry
act_model = models["askui_act"]["factory"]()
```

## Using Default Models

The simplest way to use AskUI Vision Agent is with default models. Just create a `VisionAgent` without specifying any models:

```python
from askui import VisionAgent

# Uses default models for all operations
with VisionAgent() as agent:
    # Uses default act_model
    agent.act("Open the calculator and add 5 + 3")

    # Uses default get_model
    result = agent.get("What is the result shown?")
    print(result)

    # Uses default locate_model
    agent.click("Clear button")
```

**Default models are:**
- **ActModel:** Claude Sonnet 4 via AskUI
- **GetModel:** Gemini 2.5 Flash + AskUI fallback
- **LocateModel:** AskUI vision models (text-based)

## Specifying Models at Construction

You can specify which models to use when creating the agent:

```python
from askui import VisionAgent
from askui.model_store import (
    create_askui_act_model,
    create_askui_get_model,
    create_askui_locate_model,
)

# Explicitly specify all models
with VisionAgent(
    act_model=create_askui_act_model(),
    get_model=create_askui_get_model(),
    locate_model=create_askui_locate_model(),
) as agent:
    agent.act("do something")
    result = agent.get("what's on screen?")
    agent.click("Submit")
```

### Mixing Default and Custom Models

You can specify only the models you want to customize:

```python
from askui import VisionAgent
from askui.model_store import create_askui_act_model

# Only specify act_model, others use defaults
with VisionAgent(
    act_model=create_askui_act_model(),
) as agent:
    agent.act("complex multi-step task")  # Uses specified act_model
    agent.get("what's the title?")         # Uses default get_model
    agent.click("button")                  # Uses default locate_model
```

## Per-Call Model Overrides

You can override the agent's default models for individual calls:

```python
from askui import VisionAgent
from askui.model_store import create_askui_act_model

# Custom act model for specific use case
custom_act_model = create_askui_act_model()

with VisionAgent() as agent:
    # Use default act_model
    agent.act("first task")

    # Override for this specific call
    agent.act("second task", act_model=custom_act_model)

    # Back to default act_model
    agent.act("third task")
```

This works for all three model types:

```python
from askui import VisionAgent
from askui.model_store import (
    create_askui_act_model,
    create_askui_get_model,
    create_askui_locate_model,
)

# Create custom model instances
custom_act = create_askui_act_model()
custom_get = create_askui_get_model()
custom_locate = create_askui_locate_model()

with VisionAgent() as agent:
    # Override act_model for this call
    agent.act("task", act_model=custom_act)

    # Override get_model for this call
    result = agent.get("query", get_model=custom_get)

    # Override locate_model for this call
    agent.click("button", locate_model=custom_locate)
```

## Model Settings

Each model type has its own settings class that controls behavior. Settings can be configured at the agent level or per-call.

### ActSettings

Controls behavior of ActModel operations:

```python
from askui import VisionAgent
from askui.models.shared.settings import ActSettings, MessageSettings
from askui.prompts.act_prompts import create_computer_agent_prompt

# Configure at agent level
with VisionAgent() as agent:
    # Modify agent's default act settings
    agent.act_settings.messages.max_tokens = 4096
    agent.act_settings.messages.temperature = 0.7

    # All act() calls use these settings
    agent.act("do something")

# Override per call
with VisionAgent() as agent:
    # Custom settings for this call only
    custom_settings = ActSettings(
        messages=MessageSettings(
            max_tokens=8192,
            temperature=0.5,
            system=create_computer_agent_prompt(),
        )
    )

    agent.act("complex task", act_settings=custom_settings)
```

**ActSettings properties:**
- `messages.max_tokens` (int): Maximum tokens to generate (default: 8192)
- `messages.temperature` (float): Sampling temperature 0.0-1.0 (default: None)
- `messages.system` (ActSystemPrompt | None): Custom system prompt
- `messages.betas` (list[str] | None): Beta features to enable
- `messages.thinking` (ThinkingConfigParam | None): Thinking configuration
- `messages.tool_choice` (ToolChoiceParam | None): Tool choice strategy

### GetSettings

Controls behavior of GetModel operations:

```python
from askui import VisionAgent
from askui.models.shared.settings import GetSettings

# Configure at agent level
with VisionAgent() as agent:
    agent.get_settings.max_tokens = 2048
    agent.get_settings.temperature = 0.3

    # All get() calls use these settings
    result = agent.get("what's on screen?")

# Override per call
with VisionAgent() as agent:
    custom_settings = GetSettings(
        max_tokens=4096,
        temperature=0.0,  # Deterministic output
        timeout=30.0,
    )

    result = agent.get("extract data", get_settings=custom_settings)
```

**GetSettings properties:**
- `max_tokens` (int): Maximum tokens to generate (default: 4096)
- `temperature` (float): Sampling temperature 0.0-1.0 (default: 0.5)
- `system_prompt` (GetSystemPrompt | None): Custom system prompt
- `timeout` (float | None): Request timeout in seconds

### LocateSettings

Controls behavior of LocateModel operations:

```python
from askui import VisionAgent
from askui.models.shared.settings import LocateSettings

# Configure at agent level
with VisionAgent() as agent:
    agent.locate_settings.confidence_threshold = 0.9
    agent.locate_settings.max_detections = 5

    # All locate operations use these settings
    agent.click("button")

# Override per call
with VisionAgent() as agent:
    custom_settings = LocateSettings(
        confidence_threshold=0.7,
        max_detections=10,
        timeout=10.0,
    )

    agent.click("element", locate_settings=custom_settings)
```

**LocateSettings properties:**
- `confidence_threshold` (float): Minimum confidence 0.0-1.0 (default: 0.8)
- `max_detections` (int): Maximum elements to detect (default: 10)
- `timeout` (float | None): Request timeout in seconds
- `query_type` (str | None): Query type for specific models
- `system_prompt` (LocateSystemPrompt | None): Custom system prompt

## BYOM: Bring Your Own Model

Instead of using AskUI-hosted models, you can use models directly from other providers like Anthropic, OpenAI, or custom endpoints.

### Using Anthropic Claude Models Directly

The most common use case is using Claude models directly from Anthropic with your own API key, rather than going through AskUI's API.

#### Installation

First, ensure you have the Anthropic extra installed:

```bash
pip install askui[anthropic]
```

#### Setup

Set your Anthropic API key as an environment variable:

```bash
# Linux/MacOS
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Windows PowerShell
$env:ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Or set it in your Python code:

```python
import os
os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-api-key"
```

#### Using Anthropic ActModel

Use Claude models for autonomous agent actions with `agent.act()`:

```python
from askui import VisionAgent
from askui.models.anthropic.anthropic_act_model import AnthropicActModel

# Create Anthropic act model
act_model = AnthropicActModel(
    model_id="claude-sonnet-4-20250514",  # or claude-opus-4-5-20251101
)

with VisionAgent(act_model=act_model) as agent:
    agent.act(
        "Open a browser, navigate to https://example.com, "
        "and tell me what the main headline is"
    )
```

**Available Claude Models:**
- `claude-opus-4-5-20251101` - Most capable model (best for complex tasks)
- `claude-sonnet-4-20250514` - Balanced model (good for most tasks)
- `claude-haiku-4-20250417` - Fast model (good for simple tasks)

#### Using Anthropic GetModel

Use Claude models for information extraction with `agent.get()`:

```python
from askui import VisionAgent
from askui.models.anthropic.anthropic_get_model import AnthropicGetModel

# Create Anthropic get model
get_model = AnthropicGetModel(
    model_id="claude-sonnet-4-20250514",
)

with VisionAgent(get_model=get_model) as agent:
    # Extract information from screen
    result = agent.get("What is the current page title?")
    print(result)

    # Extract structured data
    from pydantic import BaseModel

    class ProductInfo(BaseModel):
        name: str
        price: float
        in_stock: bool

    product = agent.get(
        "Extract the product information",
        response_schema=ProductInfo
    )
    print(f"Product: {product.name}, Price: ${product.price}")
```

#### Using Anthropic LocateModel

Use Claude's computer use capabilities to locate UI elements:

```python
from askui import VisionAgent
from askui.models.anthropic.anthropic_locate_model import AnthropicLocateModel

# Create Anthropic locate model
locate_model = AnthropicLocateModel(
    model_id="claude-sonnet-4-20250514",
)

with VisionAgent(locate_model=locate_model) as agent:
    # Locate and click elements
    agent.click("Submit button", locate_model=locate_model)

    # Find element coordinates
    point = agent.locate("Search field")
    print(f"Search field at: {point}")
```

#### Complete Example: All Anthropic Models

Use Anthropic models for all agent operations:

```python
import os
from askui import VisionAgent
from askui.models.anthropic.anthropic_act_model import AnthropicActModel
from askui.models.anthropic.anthropic_get_model import AnthropicGetModel
from askui.models.anthropic.anthropic_locate_model import AnthropicLocateModel

# Set your API key
os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-api-key"

# Create all Anthropic models
act_model = AnthropicActModel(model_id="claude-sonnet-4-20250514")
get_model = AnthropicGetModel(model_id="claude-sonnet-4-20250514")
locate_model = AnthropicLocateModel(model_id="claude-sonnet-4-20250514")

with VisionAgent(
    act_model=act_model,
    get_model=get_model,
    locate_model=locate_model,
) as agent:
    # All operations now use Anthropic directly
    agent.act("Navigate to the settings page")

    setting_value = agent.get("What is the current theme setting?")
    print(f"Current theme: {setting_value}")

    agent.click("Dark mode toggle")
```

#### Mixing AskUI and Anthropic Models

You can mix and match - use Anthropic for some operations and AskUI defaults for others:

```python
from askui import VisionAgent
from askui.models.anthropic.anthropic_act_model import AnthropicActModel
# get_model and locate_model will use AskUI defaults

act_model = AnthropicActModel(model_id="claude-opus-4-5-20251101")

with VisionAgent(act_model=act_model) as agent:
    # Uses Anthropic Claude Opus for complex reasoning
    agent.act("Complete the checkout process with default shipping")

    # Uses AskUI default get_model for extraction
    total = agent.get("What is the order total?")

    # Uses AskUI default locate_model for clicking
    agent.click("Confirm order")
```

#### Customizing Anthropic Settings

Configure model behavior through settings:

```python
from askui import VisionAgent
from askui.models.anthropic.anthropic_act_model import AnthropicActModel
from askui.models.shared.settings import ActSettings, MessageSettings

act_model = AnthropicActModel(model_id="claude-sonnet-4-20250514")

with VisionAgent(act_model=act_model) as agent:
    # Custom settings for this call
    custom_settings = ActSettings(
        messages=MessageSettings(
            max_tokens=16384,
            temperature=0.7,
            betas=["computer-use-2025-01-24"],  # Enable latest computer use
        )
    )

    agent.act(
        "Perform complex multi-step task",
        act_settings=custom_settings
    )
```

#### Using Anthropic Bedrock or Vertex AI

If you're using Claude through AWS Bedrock or Google Vertex AI:

```python
from askui import VisionAgent
from askui.models.anthropic.anthropic_act_model import AnthropicActModel

# For AWS Bedrock
act_model = AnthropicActModel(
    model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    api_provider="bedrock",
)

# For Google Vertex AI
act_model = AnthropicActModel(
    model_id="claude-sonnet-4-20250514",
    api_provider="vertex",
)

with VisionAgent(act_model=act_model) as agent:
    agent.act("do something")
```

### Why Use Your Own API Keys?

**Cost Control:**
- Pay directly to Anthropic at their rates
- No markup or additional fees
- Better cost tracking and budgeting

**Model Selection:**
- Access to all Claude model versions immediately
- Try beta features and new releases
- Switch between Opus, Sonnet, and Haiku based on task complexity

**Data Privacy:**
- Direct communication with Anthropic
- No intermediate services
- Full control over data flow

**Rate Limits:**
- Your own rate limits from Anthropic
- No shared quota with other users
- Predictable performance

## Best Practices

### 1. Start with Default Models

Default models are optimized and well-tested. Only create custom models when you need:
- Integration with a specific AI provider
- Custom business logic or preprocessing
- Specialized model behavior
- Cost optimization or on-premise deployment

```python
# Good: Start simple
with VisionAgent() as agent:
    agent.act("do something")

# Only customize when needed
with VisionAgent(act_model=MySpecialActModel()) as agent:
    agent.act("specialized task")
```

### 2. Use Per-Call Overrides for Experimentation

When testing different models, use per-call overrides:

```python
from askui.model_store import create_askui_act_model

experimental_model = MyExperimentalActModel()
default_model = create_askui_act_model()

with VisionAgent() as agent:
    # Most tasks use default
    agent.act("regular task 1")
    agent.act("regular task 2")

    # Test experimental model on specific tasks
    agent.act("test task", act_model=experimental_model)

    # Back to default
    agent.act("regular task 3")
```

### 3. Implement Proper Error Handling

Always handle errors gracefully in custom models:

```python
class RobustActModel(ActModel):
    @override
    def act(
        self,
        messages: list[MessageParam],
        act_settings: ActSettings,
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
    ) -> None:
        try:
            # Your implementation
            self._execute_actions(messages, act_settings, tools)
        except ConnectionError as e:
            error_msg = f"Failed to connect to AI service: {e}"
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error in act model: {e}"
            raise RuntimeError(error_msg) from e
```

### 4. Add Logging for Debugging

Implement logging to help with troubleshooting:

```python
import logging

logger = logging.getLogger(__name__)

class LoggedActModel(ActModel):
    @override
    def act(
        self,
        messages: list[MessageParam],
        act_settings: ActSettings,
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
    ) -> None:
        logger.info(f"Act called with {len(messages)} messages")
        logger.debug(f"Settings: max_tokens={act_settings.messages.max_tokens}")

        # Your implementation

        logger.info("Act completed successfully")
```

### 5. Make Models Configurable

Use configuration objects for flexibility:

```python
from dataclasses import dataclass

@dataclass
class MyModelConfig:
    api_endpoint: str
    api_key: str
    timeout: float = 30.0
    max_retries: int = 3
    enable_caching: bool = True

class ConfigurableActModel(ActModel):
    def __init__(self, config: MyModelConfig):
        self.config = config

    @override
    def act(
        self,
        messages: list[MessageParam],
        act_settings: ActSettings,
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
    ) -> None:
        # Use configuration
        timeout = self.config.timeout
        retries = self.config.max_retries

        # Your implementation using config
```

### 6. Respect Settings Parameters

Always use the settings parameters provided:

```python
class WellBehavedGetModel(GetModel):
    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        get_settings: GetSettings,
    ) -> ResponseSchema | str:
        # Respect max_tokens
        max_tokens = get_settings.max_tokens

        # Respect temperature
        temperature = get_settings.temperature

        # Respect timeout
        timeout = get_settings.timeout or 30.0

        # Use these in your API call
        result = self._call_api(
            query=query,
            source=source,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )

        return result
```

### 7. Use Caching for Efficiency

For models that involve expensive initialization, use caching:

```python
from functools import cache

@cache
def create_expensive_model() -> ActModel:
    """Create model with expensive initialization (cached)."""
    # This initialization only happens once
    return MyExpensiveActModel(
        load_weights="large-model.bin",
        initialize_gpu=True,
    )

# First call: initializes model
model1 = create_expensive_model()

# Second call: returns cached instance
model2 = create_expensive_model()

assert model1 is model2  # Same instance
```

### 8. Handle Response Schemas Correctly

For GetModels, respect the `response_schema` parameter:

```python
class SmartGetModel(GetModel):
    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        get_settings: GetSettings,
    ) -> ResponseSchema | str:
        # Call your AI model
        raw_response = self._call_ai_model(query, source)

        # If response_schema is provided, parse to that structure
        if response_schema is not None:
            if response_schema in (bool, int, float, str):
                # Handle primitive types
                return response_schema(raw_response)
            else:
                # Parse to Pydantic model
                return response_schema.model_validate_json(raw_response)

        # Otherwise return as string
        return str(raw_response)
```

### 9. Test with Simple Cases First

When developing custom models, test with simple cases:

```python
# Test act model with simple goal
with VisionAgent(act_model=MyCustomActModel()) as agent:
    agent.act("print hello")  # Start simple

# Test get model with simple query
with VisionAgent(get_model=MyCustomGetModel()) as agent:
    result = agent.get("What color is the screen?")  # Simple query

# Test locate model with obvious element
with VisionAgent(locate_model=MyCustomLocateModel()) as agent:
    point = agent.locate("large button in center")  # Easy to find
```

### 10. When to Use Each Model Type

Choose the right model type for your use case:

| Use Case | Model Type | Example |
|----------|-----------|---------|
| Multi-step automation | ActModel | "Log in and submit the form" |
| Information extraction | GetModel | "What's the price shown?" |
| Single-step interactions | LocateModel | "Click the Submit button" |
| Data validation | GetModel | "Is this a login page?" |
| Screen navigation | ActModel | "Navigate to settings" |
| UI element finding | LocateModel | "Find all buttons on screen" |

```python
with VisionAgent() as agent:
    # Use act() for complex workflows
    agent.act("Complete the checkout process with these details...")

    # Use get() for extracting information
    total = agent.get("What is the order total?")

    # Use click() for simple interactions (uses locate_model)
    agent.click("Confirm order")
```

## Migration from Old System

If you're migrating from the old ModelRouter/ModelRegistry system, here are the key changes:

### Old Pattern (No Longer Works)
```python
# OLD - This is removed
from askui import VisionAgent

with VisionAgent(model="askui") as agent:  # model parameter removed
    agent.click("button", model="askui-pta")  # model parameter removed
```

### New Pattern
```python
# NEW - Direct model instances
from askui import VisionAgent
from askui.model_store import (
    create_askui_act_model,
    create_askui_locate_model,
)

with VisionAgent(
    act_model=create_askui_act_model(),
    locate_model=create_askui_locate_model(),
) as agent:
    agent.click("button")
```

### Old Pattern: Model Composition
```python
# OLD - model parameter with dict
with VisionAgent(model={
    "act": "claude-sonnet-4-20250514",
    "get": "askui",
    "locate": "askui-combo"
}) as agent:
    pass
```

### New Pattern: Direct Model Instances
```python
# NEW - model instances at construction
from askui.model_store import (
    create_askui_act_model,
    create_askui_get_model,
    create_askui_locate_model,
)

with VisionAgent(
    act_model=create_askui_act_model(),
    get_model=create_askui_get_model(),
    locate_model=create_askui_locate_model(),
) as agent:
    pass
```

The new system provides better type safety, clearer semantics, and more flexibility for custom model implementations.
