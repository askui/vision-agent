# Model System Simplification Concept

## Summary

### WHY?
The current ModelRouter and ModelRegistry architecture introduces unnecessary complexity with 7+ layers of indirection, string-based model lookups, mixed factory patterns, and agent-level settings that expose model internals. This makes the codebase difficult to maintain, extend, and debug, while providing a confusing API for users.

### WHAT?
We are removing ModelRouter and ModelRegistry entirely, replacing them with direct model instance injection. Settings will be stored ONLY at the agent level (single source of truth) and passed to models when called. Models become lightweight and only store their `model_id`. This is a **breaking change with no backward compatibility** in a single release.

### HOW?

**Architecture Changes:**
- **Direct injection**: Users provide model instances (`ClaudeActModel(model_id="...")`) instead of strings (`"claude"`)
- **Lightweight models**: Models only store `model_id`, no settings
  - `ClaudeActModel(model_id="claude-sonnet-4")` - just the ID
  - `GeminiGetModel(model_id="gemini-2.5-flash")` - just the ID
  - `AskUiLocateModel()` - no parameters
- **Agent-level settings**: Settings stored ONLY at agent level (single source of truth)
  - `agent.act_settings`, `agent.get_settings`, `agent.locate_settings` as member variables
  - Platform-specific defaults (VisionAgent vs AndroidVisionAgent)
  - Persistent modification: `agent.act_settings.messages.temperature = 0.9`
  - Per-call override: `agent.act("task", act_settings=temp_settings)`
- **Settings passed to models**: Agent passes settings when calling model methods
  - `model.act(..., act_settings=settings)`
- **Type safety**: Each model type has its own Settings class with appropriate fields
- **Model discovery**: New `askui.model_store` module with `list_available_models()` for discovery

**Model Types & BYOM:**
- **ActModel**: Complex agentic loop - BYOM via `AskUIAgent` + custom `MessagesApi`
- **GetModel**: Data extraction - direct interface implementation (BYOM rarely needed)
- **LocateModel**: Element location - direct interface implementation (BYOM rarely needed)

**What's Removed (~600 LOC):**
- ModelRouter class and all routing logic
- ModelRegistry and initialization
- Prefix-based routing and model name transformation
- String-based model selection at agent level

**What's Added (~200 LOC):**
- `GetSettings` and `LocateSettings` classes
- `askui.model_store` module for model discovery
- `FallbackModel` for simple composition
- Factory functions per provider (e.g., `create_claude_act_model()`)
- Settings parameters in agent methods for per-call override
- Settings parameters in model method signatures

**Migration:**
- Users must update from `VisionAgent(model="askui")` to `VisionAgent(act_model=AskUiActModel())`
- Settings remain at agent level (no change to user experience here)
- Models become lightweight (only store model_id)
- Major version bump with comprehensive migration guide
- No backward compatibility - users pin to old version if not ready

**Result:** Simpler, more maintainable architecture with better type safety, clearer execution flow, single source of truth for settings, and stateless/reusable models.

---

## 0. Terminology Clarification

To avoid confusion, we use distinct terms for two different concepts:

- **Model** (or **Model Wrapper**): The Python object that implements `ActModel`, `GetModel`, or `LocateModel` interfaces. This is the adapter/handler that knows how to interact with an AI provider.
  - Example: `claude_model = ClaudeActModel(model_id="claude-sonnet-4-20250514")`

- **Model ID**: The string identifier for the specific LLM to use (e.g., `"claude-sonnet-4-20250514"`, `"gpt-4"`). This is configured in the model's constructor and used internally.
  - Example: The `model_id` is stored in the model instance and passed to the provider's API

**Important:** The `model_id` is an **internal parameter** of the model, not exposed in agent methods:

```python
# Configure model with model_id
claude_sonnet = ClaudeActModel(model_id="claude-sonnet-4-20250514")
claude_opus = ClaudeActModel(model_id="claude-opus-4-5-20251101")

# Use in agent (no model_id parameter in agent methods)
agent = VisionAgent(act_model=claude_sonnet)
agent.act("Click button")  # Uses claude-sonnet-4-20250514 internally

# Override by providing different model instance
agent.act("Complex task", act_model=claude_opus)  # Uses claude-opus-4-5-20251101
```

---

## 1. Current Architecture Problems

### 1.1 Excessive Indirection
```
User → AgentBase → ModelRouter → Registry → Factory → Model → Facade → Sub-models
```
This creates 7+ layers between user action and actual model execution.

### 1.2 Complex Model Resolution
Three-level model selection with string-based lookups:
```python
agent = VisionAgent(model="askui")  # Agent-level
agent = VisionAgent(model={"act": "claude", "locate": "askui-pta"})  # Task-level
agent.click("button", model="custom-locate")  # Method-level
```

Requires:
- String-to-model resolution at runtime
- Prefix-based routing (`"anthropic/"`, `"bedrock/"`)
- Model name transformation
- Error handling for missing models

### 1.3 Factory Pattern Overhead
Mixed instance/callable pattern in registry:
```python
{
    "model-1": MyModel(),  # Instance
    "model-2": lambda: MyModel(),  # Factory
}
```

Requires `isinstance()` checks and lazy initialization logic throughout.

### 1.4 Unclear Extension Points
Users have multiple ways to customize:
- Implement `ActModel`/`GetModel`/`LocateModel`
- Implement `MessagesApi`
- Provide custom registry
- Use factory functions

This creates confusion about the "right" way to extend the system.

---

## 2. Proposed Architecture

### 2.1 Core Principle: Direct Injection over Registry Lookup

**Before (Registry-based):**
```python
# User provides string names
agent = VisionAgent(model="askui")

# Framework looks up in registry
model_router = ModelRouter(registry={"askui": AskUiModel()})
model = model_router.get_model("askui")
```

**After (Direct injection):**
```python
# User provides model instances directly
agent = VisionAgent(act_model=AskUiModel())

# Framework uses the instance directly
model = self._model
```

### 2.2 Model Selection: One Level Instead of Three

**Simplified Model Choice:**
```python
# Only Task-specific models
agent = VisionAgent(
    act_model=ClaudeActModel(), #users can add a model id, an endpoint and api key, or even a messagesAPI to the constructor of the models to support BYOM capabilities
    get_model=AskUiGetModel(),
    locate_model=AskUiLocateModel()
)

# Method-level override (optional)
agent.click("button", locate_model=CustomLocateModel())
```

**Benefits:**
- No string-based lookup required
- Clear type hints in IDE
- Compile-time type checking
- Simpler mental model

### 2.3 Default Models: Lazy Module-Level Singletons

Instead of complex registry initialization, use simple module-level defaults:

```python
# src/askui/models/defaults.py

from functools import cache

@cache
def default_act_model() -> ActModel:
    """Returns the default ActModel (AskUI)."""
    return AskUiActModel()

@cache
def default_get_model() -> GetModel:
    """Returns the default GetModel (AskUI)."""
    return AskUiGetModel()

@cache
def default_locate_model() -> LocateModel:
    """Returns the default LocateModel (AskUI)."""
    return AskUiLocateModel()

# Usage in AgentBase
class AgentBase:
    def __init__(
        self,
        act_model: ActModel | None = None,
        get_model: GetModel | None = None,
        locate_model: LocateModel | None = None,
        **kwargs
    ):
        # Resolve models
        self._act_model = act_model or default_act_model()
        self._get_model = get_model or default_get_model()
        self._locate_model = locate_model or default_locate_model()
```

**Benefits:**
- No registry or router needed
- Lazy initialization via `@cache`
- Clear default behavior
- Easy to override

### 2.4 Custom Models: Different Approaches for Different Model Types

The three model types have fundamentally different characteristics:

**ActModel (Agentic Loop)**
- Complex tool-calling loop with message history
- **BYOM Supported**: Use `AskUIAgent` with custom `MessagesApi`
- Primary extension point for custom LLMs

**GetModel (Data Extraction)**
- Extracts structured/unstructured data from images/PDFs
- **BYOM Not Needed**: AskUI provides excellent defaults; custom implementations rare
- Users can implement interface directly if needed

**LocateModel (Element Location)**
- Finds UI element coordinates
- **BYOM Not Needed**: AskUI provides excellent defaults; custom implementations rare
- Users can implement interface directly if needed

---

**Approach A: Custom ActModel via AskUIAgent + MessagesApi (BYOM)**
```python
from askui import VisionAgent
from askui.model_store.act_models.agent import AskUIAgent
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.agent_message_param import MessageParam

class MyMessagesApi(MessagesApi):
    def create_message(self, messages, model_id, tools, **kwargs):
        # Custom API integration for your LLM provider
        response = my_provider.chat(messages=messages, model=model_id, tools=tools)
        return MessageParam.model_validate(response)

# AskUIAgent configured with custom MessagesApi
my_act_model = AskUIAgent(
    messages_api=MyMessagesApi(),
    model_id="my-custom-llm-v2"
)

agent = VisionAgent(act_model=my_act_model)
agent.act("Click the submit button")
```

**Approach B: Configure Predefined ActModels**
```python
from askui import VisionAgent
from askui.models import ClaudeActModel

# Configure Claude with custom endpoint/API key
my_act_model = ClaudeActModel(
    endpoint="https://my-claude-proxy.com/messages",
    api_key="my-api-key",
    model_id="claude-sonnet-4-20250514"
)

agent = VisionAgent(act_model=my_act_model)
```

**Approach C: Implement Model Interfaces Directly (Rare)**
```python
from askui import VisionAgent
from askui.models import GetModel, GetSettings, ResponseSchema

class MyGetModel(GetModel):
    def __init__(self, model_id: str):
        self._model_id = model_id

    def get(self, query, source, response_schema, get_settings: GetSettings) -> ResponseSchema | str:
        # Custom extraction logic (receives settings from agent)
        return "extracted data"

agent = VisionAgent(get_model=MyGetModel(model_id="my-custom-model-v1"))
```

**Benefits:**
- Clear extension points: `MessagesApi` for ActModel BYOM, direct interfaces for rare custom cases
- No registry required
- Direct, explicit configuration
- Better type safety

### 2.5 Model Configuration: Separation of ID and Settings

**Key Principle:** Settings are stored ONLY at the agent level, while models only store their `model_id`. This creates a single source of truth and avoids contradictory settings.

#### Current Problem
Settings are currently at the agent level with unclear ownership:
```python
# Current (settings at agent level - confusing!)
agent = VisionAgent()
agent.act_settings.messages.max_tokens = 8192  # Agent knows about model internals
agent.act("Click button", settings=custom_settings)  # Settings passed per-call
```

**Issues:**
- Agent knows about model-specific internals (Anthropic betas, thinking config)
- Settings passed per-call create confusion about defaults
- No type safety for model-specific settings
- Unclear whether settings should be in agent or model

#### Proposed Solution: Settings at Agent Level, Passed to Models

**Models are lightweight and only store `model_id`:**

```python
from askui import VisionAgent
from askui.models import ClaudeActModel, GeminiGetModel, AskUiLocateModel

# Models are lightweight - only store model_id (NO settings)
claude_sonnet = ClaudeActModel(model_id="claude-sonnet-4-20250514")
claude_opus = ClaudeActModel(model_id="claude-opus-4-5-20251101")
gemini_get = GeminiGetModel(model_id="gemini-2.5-flash")
askui_locate = AskUiLocateModel()  # No model_id for AskUI models

# Agent stores ALL settings - single source of truth
agent = VisionAgent(
    act_model=claude_sonnet,
    get_model=gemini_get,
    locate_model=askui_locate
)

# Agent has platform-specific settings as mutable member variables
# (created automatically in __init__ based on agent type)
print(agent.act_settings)      # ActSettings with desktop defaults
print(agent.get_settings)      # GetSettings with defaults
print(agent.locate_settings)   # LocateSettings with defaults
```

**Agent stores settings with platform-specific defaults:**

```python
from askui.models import ActSettings, GetSettings, LocateSettings, MessageSettings, ActSystemPrompt
from askui.prompts.act_prompts import create_computer_agent_prompt, create_android_agent_prompt

# VisionAgent (Desktop) - platform-specific defaults
class VisionAgent(AgentBase):
    def __init__(self, act_model=None, get_model=None, locate_model=None, **kwargs):
        # Settings stored ONLY at agent level
        self.act_settings = ActSettings(
            messages=MessageSettings(
                max_tokens=4096,
                temperature=0.7,
                system=create_computer_agent_prompt()
            )
        )
        self.get_settings = GetSettings(max_tokens=4096, temperature=0.5)
        self.locate_settings = LocateSettings(confidence_threshold=0.8)

        # Models are lightweight (no settings, just model_id)
        self._act_model = act_model or default_act_model()
        self._get_model = get_model or default_get_model()
        self._locate_model = locate_model or default_locate_model()

    def act(self, instruction, act_model=None, act_settings=None, **kwargs):
        model = act_model or self._act_model
        settings = act_settings or self.act_settings  # Use override or agent's settings
        # Agent passes settings to model
        model.act(messages=..., tools=..., act_settings=settings)

# AndroidVisionAgent (Mobile) - different platform-specific defaults
class AndroidVisionAgent(AgentBase):
    def __init__(self, act_model=None, **kwargs):
        # Different defaults for Android
        self.act_settings = ActSettings(
            messages=MessageSettings(
                system=create_android_agent_prompt()
            )
        )
        # ... similar for get_settings and locate_settings
```

**Usage Pattern 1: Persistent Modification**
```python
agent = VisionAgent()

# Modify agent's settings directly - changes persist across all calls
agent.act_settings.messages.system.ui_information = "Banking app with dark theme"
agent.act_settings.messages.system.additional_rules += "\nAlways verify balance"

# All subsequent calls use modified settings
agent.act("Login to account")  # Uses modified settings
agent.act("Check balance")     # STILL uses modified settings
agent.act("Transfer money")    # STILL uses modified settings
```

**Usage Pattern 2: Per-Call Override**
```python
agent = VisionAgent()

# Normal call uses agent's settings
agent.act("Simple task")

# Override settings for this one call only
temp_settings = ActSettings(
    messages=MessageSettings(
        max_tokens=16384,
        temperature=0.9
    )
)
agent.act("Complex task", act_settings=temp_settings)

# Next call reverts to agent's settings
agent.act("Another task")  # Back to agent.act_settings
```

**Usage Pattern 3: Switch Models (Same Settings)**
```python
# Create lightweight model instances (just model_id, no settings)
claude_sonnet = ClaudeActModel(model_id="claude-sonnet-4-20250514")
claude_opus = ClaudeActModel(model_id="claude-opus-4-5-20251101")

agent = VisionAgent(act_model=claude_sonnet)

# Uses claude-sonnet with agent's settings
agent.act("Simple task")

# Override model for complex task (still uses agent's settings)
agent.act("Complex task", act_model=claude_opus)

# Can even reuse same model instance with different agents
agent1 = VisionAgent(act_model=claude_sonnet)  # Desktop settings
agent2 = AndroidVisionAgent(act_model=claude_sonnet)  # Android settings
```

**Benefits:**
- ✅ **Single source of truth**: Settings stored ONLY at agent level
- ✅ **No contradictory settings**: Can't have conflicting settings between model and agent
- ✅ **Stateless models**: Models are lightweight and reusable across agents
- ✅ **Same model, different settings**: One model instance can be used with different agents/settings
- ✅ **Platform-specific defaults**: Each agent type (VisionAgent, AndroidVisionAgent) has appropriate defaults
- ✅ **Persistent modification**: Modify `agent.act_settings` directly for all future calls
- ✅ **Per-call override**: Pass `act_settings` parameter for one-off customization
- ✅ **Type safety**: Each model type has its own Settings class
- ✅ **Simple mental model**: Settings live on agent, models just know which LLM to call
- ✅ **Clearer separation**: Models = "which LLM", Agent = "how to use it"

**Constructor Signatures:**

```python
# ActModel implementations (only model_id, no settings)
ClaudeActModel(model_id: str)
AskUIAgent(model_id: str, messages_api: MessagesApi)

# GetModel implementations (only model_id, no settings)
GeminiGetModel(model_id: str)
AskUiGetModel()  # No model_id for AskUI

# LocateModel implementations (only model_id, no settings)
AskUiLocateModel()  # No model_id
ClaudeLocateModel(model_id: str)
```

**Settings Classes:**

| Model Type | Settings Class | Key Fields |
|------------|---------------|-----------|
| **ActModel** | `ActSettings` (exists) | `messages: MessageSettings` (contains max_tokens, temperature, system: ActSystemPrompt, thinking, tool_choice, betas) |
| **GetModel** | `GetSettings` (NEW) | `max_tokens`, `temperature`, `system_prompt: GetSystemPrompt \| None`, `timeout` |
| **LocateModel** | `LocateSettings` (NEW) | `query_type`, `confidence_threshold`, `max_detections`, `timeout`, `system_prompt: LocateSystemPrompt \| None` |

**Note:** `ActSettings` already exists in `src/askui/models/shared/settings.py`. Need to create `GetSettings` and `LocateSettings`.

**Migration Impact:**
```python
# OLD: Settings at agent level only
agent = VisionAgent(model="claude")
agent.act_settings.messages.max_tokens = 8192
agent.act("task", settings=ActSettings(messages=MessageSettings(temperature=0.5)))

# NEW: Still at agent level, but cleaner
claude = ClaudeActModel(model_id="claude-sonnet-4")  # Lightweight, no settings
agent = VisionAgent(act_model=claude)
agent.act_settings.messages.max_tokens = 8192  # Modify agent's settings
agent.act("task")  # Uses agent's settings
# Or override per-call
agent.act("task", act_settings=ActSettings(...))
```

**What Changes:**
- ✅ Keep `act_settings`, `get_settings`, `locate_settings` attributes on agent
- ✅ Add `act_settings`, `get_settings`, `locate_settings` parameters to agent methods for per-call override
- ✅ Keep `ActSettings` and `MessageSettings` as-is (no model_id field)
- ✅ Create new `GetSettings` class in `src/askui/models/shared/settings.py`
- ✅ Create new `LocateSettings` class in `src/askui/models/shared/settings.py`
- ✅ Model constructors: only `model_id` parameter (no settings)
- ✅ Model method signatures: add `act_settings`, `get_settings`, `locate_settings` parameters

**Example Model Implementation:**
```python
class ClaudeActModel(ActModel):
    def __init__(self, model_id: str):
        # Only stores model_id (no settings)
        self._model_id = model_id
        self._messages_api = create_anthropic_messages_api()

    def act(self, messages, on_message, tools, act_settings: ActSettings):
        # Receives settings as parameter (doesn't store them)
        return self._messages_api.create_message(
            messages=messages,
            model_id=self._model_id,
            tools=tools,
            **act_settings.messages.model_dump()
        )
```

---

## 3. Detailed Component Changes

### 3.1 Remove Components

**Delete entirely:**
- `src/askui/models/model_router.py` (ModelRouter class)
- Registry initialization logic in `src/askui/models/models.py`
- Prefix-based routing logic
- Factory function handling code
- Model name transformation logic

**Estimated removal:** ~800 lines of code

### 3.2 New Components

**Add:**
- `src/askui/models/defaults.py` - Default model factories (~50 lines)
- `src/askui/model_store/` - Model discovery and listing (~50 lines)

**Estimated addition:** ~200 lines of code

**Net reduction:** ~600 lines

### 3.3 Modified Components

#### AgentBase Constructor
**Before:**
```python
def __init__(
    self,
    model: TotalModelChoice = ModelName.ASKUI,
    models: ModelRegistry | None = None,
    **kwargs
):
    self._model = self._init_model(model)
    self._model_router = ModelRouter(models or initialize_default_model_registry())
```

**After:**
```python
def __init__(
    self,
    act_model: ActModel | None = None,
    get_model: GetModel | None = None,
    locate_model: LocateModel | None = None,
    **kwargs
):
    # Settings stored at agent level (platform-specific defaults)
    self.act_settings = self._create_default_act_settings()  # Subclass-specific
    self.get_settings = GetSettings()  # Common defaults
    self.locate_settings = LocateSettings()  # Common defaults

    # Models - simple resolution, no router needed
    self._act_model = act_model or default_act_model()
    self._get_model = get_model or default_get_model()
    self._locate_model = locate_model or default_locate_model()
```

**Example subclass implementation:**
```python
class VisionAgent(AgentBase):
    def _create_default_act_settings(self) -> ActSettings:
        return ActSettings(
            messages=MessageSettings(
                system=create_computer_agent_prompt()
            )
        )

class AndroidVisionAgent(AgentBase):
    def _create_default_act_settings(self) -> ActSettings:
        return ActSettings(
            messages=MessageSettings(
                system=create_android_agent_prompt()
            )
        )
```

#### AgentBase Methods
**Before:**
```python
def click(self, locator, model=None, **kwargs):
    model_name = self._get_model(model, "locate")
    point = self._model_router.locate(locator, screenshot, model_name)
    self._toolbox.os.click(point.x, point.y)
```

**After:**
```python
def click(self, locator, locate_model: LocateModel | None = None, locate_settings: LocateSettings | None = None, **kwargs):
    model = locate_model or self._locate_model
    settings = locate_settings or self.locate_settings
    # Agent passes settings to model
    point = model.locate(locator, screenshot, locate_settings=settings)
    self._toolbox.os.click(point.x, point.y)

def act(self, instruction, act_model: ActModel | None = None, act_settings: ActSettings | None = None, **kwargs):
    model = act_model or self._act_model
    settings = act_settings or self.act_settings
    # Agent passes settings to model
    model.act(messages=..., tools=..., act_settings=settings)

def get(self, query, get_model: GetModel | None = None, get_settings: GetSettings | None = None, **kwargs):
    model = get_model or self._get_model
    settings = get_settings or self.get_settings
    # Agent passes settings to model
    return model.get(query=query, source=..., get_settings=settings)
```

### 3.4 Preserve Components

**Keep unchanged:**
- `ActModel`, `GetModel`, `LocateModel` interfaces - core abstractions are sound
- `MessagesApi` abstraction - provides provider flexibility
- `Agent` class - generic ActModel implementation
- Model implementations (Anthropic, AskUI, OpenRouter, etc.)
- `ModelFacade` - simplified version for composition

---

## 4. Model Composition Simplification

### 4.1 Current Approach: Complex Composition
```python
# Current: Mix of CompositeModel and fallback logic
askui_pta = AskUiApiHandler(query_type="clickable")
askui_ocr = AskUiApiHandler(query_type="text")
askui_ai = AskUiApiHandler(query_type="ai-element")

composition = ModelComposition(
    models=[askui_pta, askui_ocr, askui_ai],
    strategy="fallback"
)
```

### 4.2 Proposed Approach: Simple Fallback Chain
```python
# New: Simple fallback chain with first-success semantics
class FallbackModel(GetModel, LocateModel, ActModel):
    """Tries models in sequence until one succeeds."""

    def __init__(self, models: list[GetModel]|list[LocateModel]|List[ActModel]):
        self._models = models

    def locate(self, locator, image, locate_settings: LocateSettings) -> Point:
        errors = []
        for m in self._models:
            try:
                return m.locate(locator, image, locate_settings=locate_settings)
            except ElementNotFoundError as e:
                errors.append(e)
                continue

        error_msg = f"All models failed: {errors}"
        raise ElementNotFoundError(error_msg)

    # would also implement get and act methods with similar logic
    # def get(self, query, source, response_schema, get_settings: GetSettings)
    # def act(self, messages, on_message, tools, act_settings: ActSettings)

# Usage
# Note: Query type would be configured via LocateSettings at agent level
askui_locate = FallbackModel([
    AskUiLocateModel(),  # Lightweight, no settings
    AskUiOcrLocateModel(),
    AskUiAiElementLocateModel(),
])

agent = VisionAgent(locate_model=askui_locate)
# Configure locate settings at agent level
agent.locate_settings.query_type = "clickable"
```

**Benefits:**
- Clear semantics: try each model in order
- No strategy pattern needed
- Easy to understand and debug
- Can be extended for other composition patterns (parallel, voting, etc.)

---

## 5. Migration Path for Users

### 5.1 Breaking Changes

**Old API (deprecated):**
```python
# String-based model selection
agent = VisionAgent(model="askui")
agent = VisionAgent(model={"act": "claude", "locate": "askui-pta"})

# Custom registry
registry = {"my-model": MyModel()}
agent = VisionAgent(models=registry, model="my-model")
```

**New API:**
```python
# Direct model instances (lightweight, only model_id)
agent = VisionAgent(
    act_model=AskUiActModel(),
    get_model=AskUiGetModel(),
    locate_model=AskUiLocateModel()
)

# Or with Claude
agent = VisionAgent(
    act_model=ClaudeActModel(model_id="claude-sonnet-4-20250514"),
    locate_model=AskUiLocateModel()
)

# Custom model
agent = VisionAgent(act_model=MyCustomActModel(model_id="my-model-v1"))
```

### 5.2 Migration Strategy

**Clean Break Approach** - No backward compatibility, single release:

1. **Remove old code entirely:**
   - Delete ModelRouter and ModelRegistry
   - Delete string-based model selection logic
   - Delete prefix-based routing
   - Delete model name transformation

2. **Implement new API:**
   - Direct model instance injection
   - Factory functions for common providers
   - Model store for discovery

3. **Update all examples and documentation:**
   - Migration guide showing before/after
   - Updated examples using new API
   - Clear documentation of breaking changes

4. **Communication:**
   - Major version bump
   - Detailed changelog
   - Migration guide in docs
   - Release notes highlighting breaking changes

**For users who can't migrate immediately:**
- Pin to the previous version until ready to upgrade
- Use migration guide to update code incrementally

---

## 6. Provider-Specific Models Simplification

### 6.1 Current Approach: Complex Facades

**Current:**
```python
def anthropic_facade(provider: str) -> ModelFacade:
    messages_api = anthropic_messages_api(provider)
    return ModelFacade(
        act_model=Agent(messages_api=messages_api),
        get_model=AnthropicModel(messages_api=messages_api, operation="get"),
        locate_model=AnthropicModel(messages_api=messages_api, operation="locate"),
    )

# Registry
{
    "claude-sonnet-4": anthropic_facade("anthropic"),
    "anthropic/claude-sonnet-4": anthropic_facade("anthropic"),
    "bedrock/claude-sonnet-4": anthropic_facade("bedrock"),
}
```

### 6.2 Proposed Approach: Simple Factory Functions

**New:**
```python
# src/askui/models/anthropic/factory.py

def create_claude_act_model(
    api_key: str | None = None,
    provider: str = "anthropic",  # "anthropic", "bedrock", "vertex"
    model_id: str = "claude-sonnet-4-20250514",
) -> ClaudeActModel:
    """Creates a Claude ActModel for agentic tasks.

    Args:
        api_key (str, optional): API key for authentication.
        provider (str): Provider to use ("anthropic", "bedrock", "vertex").
        model_id (str): The specific Claude model to use.

    Returns:
        ClaudeActModel: A model instance that implements ActModel.
    """
    messages_api = create_anthropic_messages_api(api_key=api_key, provider=provider)
    return ClaudeActModel(messages_api=messages_api, model_id=model_id)

def create_claude_get_model(
    api_key: str | None = None,
    provider: str = "anthropic",
    model_id: str = "claude-sonnet-4-20250514",
) -> ClaudeGetModel:
    """Creates a Claude GetModel for data extraction."""
    messages_api = create_anthropic_messages_api(api_key=api_key, provider=provider)
    return ClaudeGetModel(messages_api=messages_api, model_id=model_id)

def create_claude_locate_model(
    api_key: str | None = None,
    provider: str = "anthropic",
    model_id: str = "claude-sonnet-4-20250514",
) -> ClaudeLocateModel:
    """Creates a Claude LocateModel for element location."""
    messages_api = create_anthropic_messages_api(api_key=api_key, provider=provider)
    return ClaudeLocateModel(messages_api=messages_api, model_id=model_id)

# Usage - all three tasks
agent = VisionAgent(
    act_model=create_claude_act_model(),
    get_model=create_claude_get_model(),
    locate_model=create_claude_locate_model()
)

# Or just use for specific tasks
agent = VisionAgent(
    act_model=create_claude_act_model(),
    # get_model and locate_model will use AskUI defaults
)
```

**Benefits:**
- No string-based routing
- Clear API with docstrings
- Type-safe configuration
- Easy to discover (IDE autocomplete)

### 6.3 Model Discovery via Model Store

**New module:** `src/askui/model_store/`

Provides a central location for discovering available models:

```python
# src/askui/model_store/__init__.py

from askui.models.anthropic.factory import (
    create_claude_act_model,
    create_claude_get_model,
    create_claude_locate_model,
)
from askui.models.askui.factory import (
    create_askui_act_model,
    create_askui_get_model,
    create_askui_locate_model,
)
# ... imports for other providers

def list_available_models() -> dict[str, dict[str, Any]]:
    """List all available models with their metadata.

    Returns:
        Dictionary mapping model names to their metadata including:
        - type: "act", "get", or "locate"
        - provider: "askui", "claude", "gemini", etc.
        - factory: The factory function to create the model
        - description: Human-readable description
    """
    return {
        "askui_act": {
            "type": "act",
            "provider": "askui",
            "factory": create_askui_act_model,
            "description": "AskUI agentic model for autonomous actions"
        },
        "claude_act": {
            "type": "act",
            "provider": "anthropic",
            "factory": create_claude_act_model,
            "description": "Claude Sonnet/Opus for agentic tasks"
        },
        # ... more models
    }

# Usage
from askui import model_store

# Discover available models
models = model_store.list_available_models()
for name, metadata in models.items():
    print(f"{name}: {metadata['description']}")

# Create model using factory
claude_act = model_store.list_available_models()["claude_act"]["factory"]()
agent = VisionAgent(act_model=claude_act)
```

**Benefits:**
- Central registry for discovery (without runtime lookup complexity)
- Programmatic access to available models
- Easy for users to explore options
- No magic strings - all accessed via factory functions

---

## 7. Chat API Integration

### 7.1 Current Challenge

The Chat API currently stores model names as strings in the database:

```python
class AssistantOrm(BaseOrm):
    model: str  # e.g., "claude-sonnet-4", "askui", etc.
```

This requires registry lookup to resolve names to model instances.

### 7.2 Proposed Solution: Model Serialization


**Add model serialization/deserialization:**

```python
# src/askui/chat/serialization.py

class SerializableModelConfig(TypedDict):
    act_model: dict[str, Any]  # Serialized ActModel
    get_model: dict[str, Any]  # Serialized GetModel
    locate_model: dict[str, Any]  # Serialized LocateModel

def serialize_act_model(model: ActModel) -> dict[str, Any]:
    """Serialize an ActModel instance to a dict."""
    if isinstance(model, AskUiActModel):
        return {"type": "askui_act", "config": {"model_id": model.model_id}}
    elif isinstance(model, ClaudeActModel):
        return {"type": "claude_act", "config": {"provider": model.provider, "model_id": model.model_id}}
    elif isinstance(model, AskUIAgent):
        return {"type": "askui_agent", "config": {"model_id": model.model_id, "messages_api_class": f"{model.messages_api.__module__}.{model.messages_api.__class__.__name__}"}}
    else:
        return {"type": "custom", "config": {"class_path": f"{model.__module__}.{model.__class__.__name__}"}}

def serialize_get_model(model: GetModel) -> dict[str, Any]:
    """Serialize a GetModel instance to a dict."""
    # Similar pattern for GetModel
    ...

def serialize_locate_model(model: LocateModel) -> dict[str, Any]:
    """Serialize a LocateModel instance to a dict."""
    # Similar pattern for LocateModel
    ...

def deserialize_act_model(data: dict[str, Any]) -> ActModel:
    """Deserialize a dict to an ActModel instance."""
    if data["type"] == "askui_act":
        return create_askui_act_model(**data["config"])
    elif data["type"] == "claude_act":
        return create_claude_act_model(**data["config"])
    # ... handle other types
    else:
        error_msg = f"Unknown ActModel type: {data['type']}"
        raise ValueError(error_msg)

# Similar deserialize functions for GetModel and LocateModel
```

**Update Chat API:**
```python
class AssistantOrm(BaseOrm):
    model_config: str  # JSON-serialized SerializableModelConfig

# When creating run
model_config = json.loads(assistant.model_config)
act_model = deserialize_act_model(model_config["act_model"])
get_model = deserialize_get_model(model_config["get_model"])
locate_model = deserialize_locate_model(model_config["locate_model"])
agent = VisionAgent(act_model=act_model, get_model=get_model, locate_model=locate_model)
```

**Note:** This serialization logic will be documented for the Chat API team to implement. The SDK team is only responsible for providing the model interfaces and ensuring they're serializable.

---

## 8. Implementation Checklist

**Note:** This is a clean break migration with **no backward compatibility**. All changes will be made in a single release.

### 8.1 Core Model System Changes
- [ ] Update model interfaces to use `model_id` parameter name instead of `model`
- [ ] Update `MessagesApi` to use `model_id` parameter
- [ ] Create Settings classes for each model type:
  - [ ] Keep `ActSettings` and `MessageSettings` as-is (already exist)
  - [ ] Create `GetSettings` class in `src/askui/models/shared/settings.py`
  - [ ] Create `LocateSettings` class in `src/askui/models/shared/settings.py`
- [ ] Update model implementations to be lightweight (only store `model_id`):
  - [ ] ActModel implementations: `__init__(model_id: str)` (no settings parameter)
  - [ ] GetModel implementations: `__init__(model_id: str)` (no settings parameter)
  - [ ] LocateModel implementations: `__init__()` or `__init__(model_id: str)` (no settings parameter)
- [ ] Update model method signatures to receive settings as parameters:
  - [ ] `ActModel.act(..., act_settings: ActSettings)` (required parameter)
  - [ ] `GetModel.get(..., get_settings: GetSettings)` (required parameter)
  - [ ] `LocateModel.locate(..., locate_settings: LocateSettings)` (required parameter)
- [ ] Update all model implementations to receive settings from agent (not store them)
- [ ] Remove `ModelRouter` class entirely
- [ ] Remove `ModelRegistry` type and initialization logic
- [ ] Remove prefix-based routing logic
- [ ] Remove factory function handling in router
- [ ] Remove model name transformation logic

### 8.2 AgentBase Refactoring
- [ ] Remove `_init_model()` and `_get_model()` methods from `AgentBase`
- [ ] Replace `model` parameter with `act_model`, `get_model`, `locate_model` in `AgentBase.__init__`
- [ ] Add settings storage to `AgentBase.__init__`:
  - [ ] `self.act_settings = self._create_default_act_settings()` (platform-specific, implemented in subclasses)
  - [ ] `self.get_settings = GetSettings()` (common defaults)
  - [ ] `self.locate_settings = LocateSettings()` (common defaults)
- [ ] Implement `_create_default_act_settings()` in each agent subclass (VisionAgent, AndroidVisionAgent, etc.)
- [ ] Update all agent methods to accept optional settings parameters for per-call override:
  - [ ] `act(..., act_model=None, act_settings=None)`
  - [ ] `get(..., get_model=None, get_settings=None)`
  - [ ] `locate/click/mouse_move(..., locate_model=None, locate_settings=None)`
- [ ] Update agent methods to pass settings to models: `model.act(..., act_settings=settings)`
- [ ] Update `AgentBase` to use direct model instances instead of router
- [ ] Create `src/askui/models/defaults.py` with default model factory functions

### 8.3 Model Discovery & Factory Functions
- [ ] Create `src/askui/model_store/` module for model discovery
- [ ] Implement `list_available_models()` function in model_store
- [ ] Create factory functions for each provider:
  - [ ] `create_claude_act_model()`, `create_claude_get_model()`, `create_claude_locate_model()`
  - [ ] `create_askui_act_model()`, `create_askui_get_model()`, `create_askui_locate_model()`
  - [ ] Similar factories for other providers (Gemini, OpenRouter, HuggingFace, etc.)
- [ ] Register all factory functions in model_store for discoverability

### 8.4 Model Composition
- [ ] Create `FallbackModel` class that implements ActModel, GetModel, and LocateModel
- [ ] Implement fallback logic with first-success semantics
- [ ] Add proper error handling and aggregation

### 8.5 Testing
- [ ] Remove all tests for ModelRouter and ModelRegistry
- [ ] Write tests for new direct injection API
- [ ] Write tests for AskUIAgent with custom MessagesApi
- [ ] Write tests for model_store.list_available_models()
- [ ] Write tests for FallbackModel composition
- [ ] Update integration tests to use new API

### 8.6 Documentation & Migration
- [ ] Create comprehensive migration guide documenting breaking changes
- [ ] Update all code examples to use new API
- [ ] Add terminology clarification section (Model vs Model ID)
- [ ] Document model_store usage for discovering available models
- [ ] Document BYOM approach with AskUIAgent + MessagesApi
- [ ] Add examples for each provider's factory functions
- [ ] Document Chat API serialization approach (for Chat API team reference)

### 8.7 Cleanup
- [ ] Remove all deprecated code paths
- [ ] Update type hints throughout codebase
- [ ] Remove unused imports
- [ ] Clean up model-related utility functions that are no longer needed
- [ ] Update pyproject.toml if any dependencies are no longer needed

---

## 9. Risk Assessment

### 9.1 Breaking Changes
**Risk:** High - This is a **complete API redesign** with no backward compatibility

**Impact:**
- **All existing code** using the old API will break
- Users **must** update their code to use the new model instances
- No deprecation period - clean break in a single release

**Mitigation:**
- Comprehensive migration guide with before/after examples
- Clear communication in release notes and documentation
- Version the release appropriately (major version bump)
- Provide example code for all common use cases
- Users who need the old API can pin to the previous version

**Migration Effort for Users:**
```python
# Before (OLD - will not work)
agent = VisionAgent(model="askui")
agent.click("button", model="claude")

# After (NEW - required)
from askui.model_store import create_askui_locate_model, create_claude_act_model
agent = VisionAgent(
    act_model=create_claude_act_model(),
    locate_model=create_askui_locate_model()
)
agent.click("button")
```

### 9.2 Chat API Migration
**Risk:** Medium - Database schema and code changes required

**Impact:**
- Chat API team needs to update model storage from strings to serialized configs
- Database migration required for existing assistants
- Run execution logic needs to be updated

**Mitigation:**
- Provide detailed serialization documentation for Chat API team
- Serialization functions can be provided in `askui.chat.serialization` module
- Chat API team is responsible for implementation and migration

### 9.3 Third-Party Integrations
**Risk:** Medium - All integrations will need updates

**Impact:**
- Any code importing `ModelRouter` or `ModelRegistry` will break
- Custom model implementations need to be updated to new interface signatures

**Mitigation:**
- Provide examples for all common use cases
- Document the new extension points clearly
- Offer support during migration period

### 9.4 Performance
**Risk:** Very Low - Performance will improve

**Benefit:**
- No registry lookups at runtime
- Simpler execution flow (fewer indirection layers)
- Better caching opportunities
- Reduced startup time

---

## 10. Success Metrics

### 10.1 Code Metrics
- **Lines of code:** Target 30% reduction in model management code
- **Cyclomatic complexity:** Reduce by 50% in model selection logic
- **Test coverage:** Maintain >90% coverage

### 10.2 User Experience Metrics
- **API clarity:** Fewer "how do I use custom models?" questions
- **Error messages:** More helpful type errors at compile time
- **Documentation:** Simpler examples (fewer lines to explain)

### 10.3 Maintenance Metrics
- **Bug reports:** Fewer model-related issues
- **Debug time:** Faster issue resolution with clearer stack traces
- **Onboarding:** Faster understanding for new contributors

---

## 11. Implementation Notes

### 11.1 Model Discovery Solution
**Implemented via `askui.model_store` module:**
- Central location for all available model factory functions
- `list_available_models()` provides programmatic discovery
- Metadata includes type, provider, factory function, and description
- No runtime registry lookup - discovery is separate from usage

### 11.2 Model Caching
**Default models use `@cache` decorator:**
- Default factory functions in `src/askui/models/defaults.py` use `@functools.cache`
- Ensures singleton-like behavior for default models
- Reduces initialization overhead
- Users can still create multiple instances if needed

### 11.3 Testing Improvements
**Direct injection simplifies testing:**
```python
# Easy mocking
mock_act_model = Mock(spec=ActModel)
mock_act_model.act.return_value = None
agent = VisionAgent(act_model=mock_act_model)

# Verify behavior
agent.act("click button")
mock_act_model.act.assert_called_once()
```

### 11.4 BYOM Capabilities Scoped to ActModel
**MessagesApi abstraction only for ActModel:**
- ActModel needs complex tool-calling loop → MessagesApi abstraction
- GetModel and LocateModel are simpler → direct interface implementation sufficient
- Users can still implement GetModel/LocateModel interfaces if needed
- Focus BYOM documentation on ActModel + AskUIAgent + MessagesApi

---

## 12. Alternative Approaches Considered

### 12.1 Phased Migration with Backward Compatibility
**Approach:** Keep old API working for 2-3 releases with deprecation warnings

**Pros:** Gentler migration path for users

**Cons:**
- Maintains complexity during transition period
- Two codepaths to maintain and test
- Delays the simplification benefits
- Confusing to have two ways to do the same thing

**Decision:** ❌ Rejected - Clean break is better for long-term maintainability

### 12.2 Keep Registry, Remove Router
**Approach:** Keep `ModelRegistry` but remove routing logic

**Pros:** Smaller change, less breaking

**Cons:**
- Still requires string-based lookup
- Doesn't address core complexity
- Minimal benefit for significant remaining complexity

**Decision:** ❌ Rejected - Doesn't go far enough

### 12.3 String-Based with Type Aliases
**Approach:** Use string literal types for model names
```python
ModelName = Literal["askui", "claude", "gemini"]
agent = VisionAgent(model="askui")  # Type-checked
```

**Pros:** Type safety with strings, smaller change

**Cons:**
- Still requires registry lookup at runtime
- Doesn't solve indirection problem
- Not extensible for custom models (can't add to Literal at runtime)

**Decision:** ❌ Rejected - Doesn't solve fundamental problems

### 12.4 Enum-Based Selection
**Approach:** Use enums instead of strings
```python
class Models(Enum):
    ASKUI = "askui"
    CLAUDE = "claude"

agent = VisionAgent(model=Models.ASKUI)
```

**Pros:** Type-safe selection, better than strings

**Cons:**
- Not extensible (users can't add custom models without modifying core)
- Still requires registry lookup
- Awkward API (enum members instead of objects)

**Decision:** ❌ Rejected - Not extensible for BYOM

### 12.5 Generic Models for All Three Types
**Approach:** Have AskUIAgent (ActModel), and direct model implementations for Get/Locate

**Pros:** Consistent pattern across all model types

**Cons:**
- GetModel and LocateModel don't need MessagesApi abstraction
- Over-engineering for rare use cases
- Users can just implement interfaces directly if needed
- MessagesApi is tool-calling specific (not applicable to simple Get/Locate)

**Decision:** ⚠️ Accepted - AskUIAgent provides BYOM for ActModel via MessagesApi injection

---

## 13. Conclusion

This proposal simplifies the AskUI VisionAgent library model system by:

1. **Removing complexity:** Eliminate ModelRouter and ModelRegistry (~600 LOC)
2. **Improving clarity:** Direct injection makes execution flow obvious
3. **Maintaining flexibility:** Custom models via:
   - AskUIAgent + MessagesApi (for BYOM agentic tasks)
   - Direct interface implementation (for custom Get/Locate)
4. **Enhancing type safety:** Compile-time checking instead of runtime lookups
5. **Streamlining composition:** Simple fallback chains instead of complex strategies
6. **Better discoverability:** Model store for finding available models

**The core insight:** String-based lookup and registry patterns were solving a problem (lazy initialization, provider abstraction) that can be better solved with direct injection and module-level cached factories.

**Trade-offs accepted:**
- ✅ Breaking changes without backward compatibility - cleaner long-term solution
- ✅ Users must update code - but migration is straightforward
- ✅ No string-based model selection - better type safety and clarity

**Next steps:**
1. Review this concept with the team
2. Create detailed implementation plan with task breakdown
3. Implement changes in a single release (clean break)
4. Create comprehensive migration guide
5. Communicate breaking changes clearly in release notes
