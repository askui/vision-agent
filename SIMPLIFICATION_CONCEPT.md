# Model System Simplification Concept

## WHY?
The current architecture has 7+ layers of indirection, string-based model lookups, and a `MessagesApi` abstraction too low-level for end users. This makes the codebase hard to maintain and BYOM unnecessarily complex.

## WHAT?

**Phase 1 (Completed):** Remove `ModelRouter` and `ModelRegistry`. Replace with direct model instance injection. Settings stored only at the agent level.

**Phase 2 (Current):** Three further changes:

1. **Rename `VisionAgent` → `Agent`** — The class is no longer desktop-only and the name should reflect that.

2. **Get/Locate as Tools** — `GetModel` and `LocateModel` disappear from the public API entirely. Their functionality becomes tools (`GetTool`, `LocateTool`). `agent.get()` and `agent.locate()` are thin wrappers that call these tools directly. The same tool instances are also available to the LLM in `agent.act()`'s tool-calling loop. No user-facing Act/Get/Locate model classes remain.

3. **Provider-based configuration** — Replace the `MessagesApi` abstraction with a higher-level provider concept. A provider encapsulates **endpoint, credentials, and the model to use**. BYOM requires no Python class implementation for standard API shapes.

---

## Architecture

### Provider Types

Three provider interface types drive all AI capabilities. They are named by their **technical specification**, not by the agent task they happen to power:

| Provider interface | Required capability | Supported by |
|--------------------|--------------------|-|
| `VlmProvider` | Multimodal input + tool-calling (for `act` and LLM-backed tools) | AskUI proxy, Anthropic |
| `ImageQAProvider` | Multimodal Q&A, structured output (for `get`) | Google, Anthropic |
| `DetectionProvider` | UI element coordinates from screenshot + locator (for `locate`) | AskUI locate API |

A single provider type can be reused wherever it satisfies the required interface — a `VlmProvider` can power `act` and also be used inside a tool that needs LLM reasoning.

**Providers own the model selection.** The model ID (e.g. `claude-sonnet-4-5-20251101`, `gemini-2.5-flash`) is configured on the provider, not on the agent or the tool. This keeps all AI configuration in one place.

### Configuration

```python
# Default (AskUI for everything, credentials read from env vars on first use)
agent = Agent()

# AskUI VLM with a specific Claude model
askui_vlm = AskUIVlmProvider(
    workspace_id=...,
    token=...,
    model_id="claude-opus-4-6-20260401",  # override the default
)
agent = Agent(settings=AgentSettings(vlm_provider=askui_vlm))

# Anthropic direct, specific model
anthropic_vlm = AnthropicVlmProvider(
    api_key=...,
    model_id="claude-sonnet-4-5-20251101",
)
agent = Agent(settings=AgentSettings(vlm_provider=anthropic_vlm))

# Mix providers per capability
agent = Agent(settings=AgentSettings(
    vlm_provider=AskUIVlmProvider(workspace_id=..., token=...),
    image_qa_provider=GoogleImageQAProvider(api_key=..., model_id="gemini-2.5-flash"),
))
```

`AgentSettings` holds one provider slot per interface type. Defaults are pre-configured to the AskUI hosted endpoints with sensible default model IDs. Users only override what they need.

### Get/Locate as Tools

```python
# agent.get() and agent.locate() call the respective tool directly
agent.get("What is the error message?")   # → GetTool(...)
agent.locate("Submit button")              # → LocateTool(...)

# The same tools are in the act loop — the LLM can call them too
agent.act("What is the name of the store on the image?")  # LLM may call GetTool internally
```

No `get_model` or `locate_model` parameters on agents. Tool behavior is controlled through `AgentSettings`.

---

## Built-in Providers

Each provider is a **single-purpose class** — one class, one interface. `AskUI` ships two separate provider classes: one for VLM access (via its Anthropic proxy) and one for element detection (its locate API).

| Class | Interface | Default model ID | Notes |
|-------|-----------|-----------------|-------|
| `AskUIVlmProvider` | `VlmProvider` | `claude-sonnet-4-5-20251101` | AskUI-hosted Anthropic proxy; supports Claude 4.x |
| `AskUIDetectionProvider` | `DetectionProvider` | n/a | AskUI locate/detection endpoint |
| `AnthropicVlmProvider` | `VlmProvider` | `claude-sonnet-4-5-20251101` | Direct Anthropic API |
| `AnthropicImageQAProvider` | `ImageQAProvider` | `claude-sonnet-4-5-20251101` | Direct Anthropic API |
| `GoogleImageQAProvider` | `ImageQAProvider` | `gemini-2.5-flash` | Google Gemini API |

Credentials are validated **lazily** — missing credentials surface as an error only at the first API call, not at provider construction time.

The `AgentSettings` defaults are:
- `vlm_provider` → `AskUIVlmProvider` (reads `ASKUI_WORKSPACE_ID` / `ASKUI_TOKEN` from env on first use)
- `image_qa_provider` → `GoogleImageQAProvider` (reads `GOOGLE_API_KEY` from env on first use)
- `detection_provider` → `AskUIDetectionProvider` (reads `ASKUI_WORKSPACE_ID` / `ASKUI_TOKEN` from env on first use)

---

## BYOM

```python
# Any OpenAI-compatible endpoint — model_id sent as-is to the endpoint
custom = OpenAICompatibleProvider(
    endpoint="https://my-llm.example.com/v1/chat/completions",
    api_key="sk-...",
    model_id="my-model-v2",
)
agent = Agent(settings=AgentSettings(vlm_provider=custom))

# Fully custom (implement the interface)
class MyProvider(VlmProvider):
    def create_message(self, messages, tools, **kwargs) -> MessageParam:
        ...

agent = Agent(settings=AgentSettings(vlm_provider=MyProvider()))
```

---

## What's Removed

- `ModelRouter`, `ModelRegistry`
- `ActModel`, `GetModel`, `LocateModel` from public API
- `MessagesApi` from public API
- `model_store` discovery / factory functions
- `get_model`, `locate_model`, `act_model` parameters on agents
- `VisionAgent` (replaced by `Agent`, clean break — no alias)

## What's Added

- `VlmProvider`, `ImageQAProvider`, `DetectionProvider` interfaces
- `AskUIVlmProvider`, `AskUIDetectionProvider`, `AnthropicVlmProvider`, `AnthropicImageQAProvider`, `GoogleImageQAProvider`, `OpenAICompatibleProvider`
- `AgentSettings` with provider slots (each provider carries its own `model_id`; credentials validated lazily)
- `GetTool`, `LocateTool` (wrap the former model implementations internally)
- `Agent` (replaces `VisionAgent`, clean break — no alias)
