# Refactor Plan: Conversation-Based Architecture with Caching

This document outlines the steps required to integrate the conversation-based architecture and enhanced caching system from the `feat/conversation_based_architecture` branch into the current branch (`chore/act_conversation_with_caching`), while preserving the new `model_providers` concept.

## Executive Summary

The goal is to combine:
- **Current branch**: New `model_providers` architecture (`VlmProvider`, `ImageQAProvider`, `DetectionProvider`) with clean provider abstractions
- **Feature branch**: Conversation/Speaker pattern with sophisticated caching (metadata, validation, visual verification, parameters)

---

## 1. Architecture Comparison

### 1.1 Current Branch Architecture

```
Agent
  ├── AgentSettings (provider-based configuration)
  │   ├── VlmProvider → MessagesApi adapter → ActModel
  │   ├── ImageQAProvider → GetModel adapter
  │   └── DetectionProvider → LocateModel adapter
  │
  ├── AskUIAgent (src/askui/models/shared/agent.py)
  │   └── ActModel implementation with _step() loop
  │
  └── CacheWriter (simple tool block recording)
      └── ExecuteCachedTrajectory (executes all steps in one tool call)
```

**Key Classes:**
- `VlmProvider` (abstract) - Provider interface for VLMs
- `AskUIVlmProvider`, `AnthropicVlmProvider` - Concrete providers
- `_VlmProviderMessagesApiAdapter` - Adapts VlmProvider → MessagesApi
- `AskUIAgent` (ActModel) - Tool-calling loop in `_step()` method
- `CacheWriter` - Simple recording via on_message callback

### 1.2 Feature Branch Architecture

```
Agent
  ├── Conversation (orchestrator)
  │   ├── Speakers collection
  │   │   ├── AskUIAgent (Speaker) - LLM API calls
  │   │   └── CacheExecutor (Speaker) - Cache playback
  │   │
  │   ├── TruncationStrategy (message history management)
  │   └── Tool execution in conversation loop
  │
  └── CacheManager (full caching system)
      ├── CacheParameterHandler (LLM-based parameter identification)
      ├── CacheValidator (validation strategies)
      └── Visual validation (phash/ahash)
```

**Key Classes:**
- `Speaker` (abstract) - Handler for conversation steps
- `Speakers` - Collection/manager of speakers
- `Conversation` - Main orchestrator with execution loop
- `AskUIAgent` (Speaker) - Makes LLM API calls
- `CacheExecutor` (Speaker) - Step-by-step cache replay
- `CacheManager` - Recording, playback, validation
- `CacheParameterHandler` - Parameter identification/substitution
- `CacheValidator` - Validation strategies (stale, failure count, etc.)

### 1.3 Key Conflicts & Decisions

| Aspect | Current Branch | Feature Branch | Decision |
|--------|---------------|----------------|----------|
| VLM abstraction | `VlmProvider` → adapter → `MessagesApi` | Direct `MessagesApi` | **Keep VlmProvider** - inject via Conversation |
| ActModel impl | `AskUIAgent` (ActModel) | N/A (uses Conversation) | **Rename to avoid conflict** |
| Speaker impl | N/A | `AskUIAgent` (Speaker) | **Add as AgentSpeaker** |
| Settings | `AgentSettings` with providers | `ActSettings` only | **Keep AgentSettings** |
| Caching | Simple `CacheWriter` | Full `CacheManager` | **Use CacheManager** |
| Cache execution | Single tool call | Step-by-step via Speaker | **Use Speaker pattern** |

---

## 2. Implementation Plan

### Phase 1: Add Speaker Infrastructure

**Goal:** Add the speaker/conversation pattern without breaking existing functionality.

#### Step 1.1: Create `src/askui/speaker/` directory

```
src/askui/speaker/
├── __init__.py
├── speaker.py          # Speaker ABC, SpeakerResult, Speakers
├── conversation.py     # Conversation orchestrator
├── agent_speaker.py    # LLM API speaker (renamed from AskUIAgent)
└── cache_executor.py   # Cache playback speaker
```

#### Step 1.2: Implement `speaker.py`

Copy from feature branch with these adaptations:
- No changes needed to `Speaker` ABC
- No changes needed to `SpeakerResult`
- Update `Speakers` to use `AgentSpeaker` as default (not `AskUIAgent`)

```python
# src/askui/speaker/speaker.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field
from typing_extensions import Literal

from askui.models.shared.agent_message_param import MessageParam, UsageParam

if TYPE_CHECKING:
    from askui.utils.caching.cache_manager import CacheManager
    from .conversation import Conversation

SPEAKER_RESULT_STATUS = Literal["continue", "switch_speaker", "done", "failed"]


class SpeakerResult(BaseModel):
    status: SPEAKER_RESULT_STATUS
    next_speaker: str | None = None
    messages_to_add: list[MessageParam] = Field(default_factory=list)
    usage: UsageParam | None = None


class Speaker(ABC):
    @abstractmethod
    def can_handle(self, conversation: "Conversation") -> bool: ...

    @abstractmethod
    def handle_step(
        self, conversation: "Conversation", cache_manager: "CacheManager | None"
    ) -> SpeakerResult: ...

    @abstractmethod
    def get_name(self) -> str: ...


class Speakers:
    def __init__(self, speakers: dict[str, Speaker] | None = None) -> None:
        from .agent_speaker import AgentSpeaker
        self.speakers: dict[str, Speaker] = speakers or {"AgentSpeaker": AgentSpeaker()}
        self.default_speaker: str = (
            "AgentSpeaker" if "AgentSpeaker" in self.speakers else list(self.speakers.keys())[0]
        )
    # ... rest same as feature branch
```

#### Step 1.3: Implement `agent_speaker.py`

Adapt the feature branch's `AskUIAgent` speaker, but:
- Rename class to `AgentSpeaker` to avoid conflict with existing `AskUIAgent` (ActModel)
- Access `VlmProvider` from the `Conversation` instance instead of accepting `MessagesApi` in constructor

```python
# src/askui/speaker/agent_speaker.py
from typing import TYPE_CHECKING

from askui.models.exceptions import MaxTokensExceededError, ModelRefusalError
from askui.models.shared.agent_message_param import MessageParam

from .speaker import Speaker, SpeakerResult

if TYPE_CHECKING:
    from askui.utils.caching.cache_manager import CacheManager
    from .conversation import Conversation


class AgentSpeaker(Speaker):
    """Speaker that handles LLM API calls.

    Accesses the VlmProvider from the Conversation instance.
    The VlmProvider encapsulates the model selection, credentials, and API calls.
    """

    def handle_step(
        self, conversation: "Conversation", cache_manager: "CacheManager | None"
    ) -> SpeakerResult:
        # Access VlmProvider from conversation
        vlm_provider = conversation.vlm_provider

        # Use VlmProvider.create_message() directly
        response = vlm_provider.create_message(
            messages=conversation.get_messages(),
            tools=conversation.tools,
            max_tokens=conversation.settings.messages.max_tokens,
            system=conversation.settings.messages.system,
            # ... other settings from conversation.settings
        )
        # ... rest of handle_step logic (adapted from feature branch)
```

#### Step 1.4: Implement `conversation.py`

Copy from feature branch with these adaptations:
- Keep the same execution loop logic
- Ensure it works with the current `ToolCollection` implementation
- **The Conversation holds all model_providers** (`VlmProvider`, `ImageQAProvider`, `DetectionProvider`) and injects them into speakers as needed
- Speakers can access providers via the conversation instance

```python
# src/askui/speaker/conversation.py
from askui.model_providers.vlm_provider import VlmProvider
from askui.model_providers.image_qa_provider import ImageQAProvider
from askui.model_providers.detection_provider import DetectionProvider


class Conversation:
    def __init__(
        self,
        speakers: Speakers,
        vlm_provider: VlmProvider,
        image_qa_provider: ImageQAProvider | None = None,
        detection_provider: DetectionProvider | None = None,
        reporter: Reporter = NULL_REPORTER,
        cache_manager: CacheManager | None = None,
        truncation_strategy_factory: TruncationStrategyFactory | None = None,
    ) -> None:
        self.speakers = speakers
        self.vlm_provider = vlm_provider
        self.image_qa_provider = image_qa_provider
        self.detection_provider = detection_provider
        # ... rest of init

    def start(
        self,
        messages: list[MessageParam],
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
        settings: ActSettings | None = None,
        reporters: list[Reporter] | None = None,
    ) -> None:
        """Initialize conversation state and start execution loop.

        Model providers are accessed via self.vlm_provider, etc.
        Speakers can access them via conversation.vlm_provider.
        """
        # ... execution loop
```

### Phase 2: Enhanced Caching System

**Goal:** Replace simple `CacheWriter` with full `CacheManager` system.

#### Step 2.1: Create `src/askui/utils/caching/` directory

```
src/askui/utils/caching/
├── __init__.py
├── cache_manager.py           # Main manager (from feature branch)
├── cache_parameter_handler.py # Parameter handling (from feature branch)
└── cache_validator.py         # Validation strategies (from feature branch)
```

#### Step 2.2: Add `src/askui/utils/visual_validation.py`

Copy directly from feature branch - no adaptations needed.

#### Step 2.3: Update `src/askui/models/shared/settings.py`

Merge settings from both branches:

```python
# Keep existing settings (ActSettings, GetSettings, LocateSettings)
# Add new caching settings from feature branch:

class CacheWritingSettings(BaseModel):
    """Settings for writing/recording cache files."""
    filename: str = ""
    parameter_identification_strategy: Literal["llm", "preset"] = "llm"
    llm_parameter_id_api_provider: str = "askui"
    visual_verification_method: Literal["phash", "ahash", "none"] = "phash"
    visual_validation_region_size: int = 100


class CacheExecutionSettings(BaseModel):
    """Settings for executing/replaying cache files."""
    delay_time_between_action: float = 0.5
    skip_visual_validation: bool = False
    visual_validation_threshold: int = 20


class CacheMetadata(BaseModel):
    """Metadata for cache files."""
    version: str = "0.1"
    created_at: datetime
    goal: str | None = None
    last_executed_at: datetime | None = None
    token_usage: UsageParam | None = None
    execution_attempts: int = 0
    failures: list[CacheFailure] = Field(default_factory=list)
    is_valid: bool = True
    invalidation_reason: str | None = None
    visual_validation: dict[str, Any] | None = None


class CacheFile(BaseModel):
    """Full cache file structure."""
    metadata: CacheMetadata
    trajectory: list[ToolUseBlockParam]
    cache_parameters: dict[str, str] = Field(default_factory=dict)


# Update CachingSettings to use new structure
class CachingSettings(BaseModel):
    strategy: Literal["read", "write", "both", "no"] = "no"
    cache_dir: str = ".askui_cache"
    writing_settings: CacheWritingSettings | None = None
    execution_settings: CacheExecutionSettings | None = None
```

#### Step 2.4: Update `src/askui/models/shared/agent_message_param.py`

Add `visual_representation` field to `ToolUseBlockParam`:

```python
class ToolUseBlockParam(BaseModel):
    id: str
    input: object
    name: str
    type: Literal["tool_use"] = "tool_use"
    cache_control: CacheControlEphemeralParam | None = None
    visual_representation: str | None = None  # NEW: Visual hash for cache validation

    @model_serializer(mode="wrap")
    def _serialize_model(
        self,
        serializer: core_schema.SerializerFunctionWrapHandler,
        info: core_schema.SerializationInfo,
    ) -> dict[str, Any]:
        """Exclude visual_representation when serializing for API."""
        data = serializer(self)
        if info.context and info.context.get("for_api", False):
            data.pop("visual_representation", None)
        return data
```

#### Step 2.5: Update caching tools

Replace/update `src/askui/tools/caching_tools.py`:
- `RetrieveCachedTestExecutions` - Add support for cache metadata, validation status
- `ExecuteCachedTrajectory` - Change to trigger speaker switch rather than execute inline
- Add `VerifyCacheExecution` tool for post-execution verification

### Phase 3: Integrate Conversation into Agent

**Goal:** Update `Agent.act()` to use the conversation-based architecture.

#### Step 3.1: Update `src/askui/agent_base.py`

Modify `act()` method to use `Conversation`:

```python
def act(
    self,
    goal: str | list[MessageParam],
    act_settings: ActSettings | None = None,
    on_message: OnMessageCb | None = None,
    tools: list[Tool] | ToolCollection | None = None,
    speakers: Speakers | None = None,  # NEW
    caching_settings: CachingSettings | None = None,
) -> None:
    # ... existing setup code ...

    # Build speakers
    _speakers = speakers or self._build_speakers(caching_settings)

    # Build tools
    _tools = self._build_tools(tools)

    # Setup caching
    cache_manager = self._setup_caching(caching_settings, _act_settings, _tools, goal_str)

    # Create conversation with model providers from AgentSettings
    conversation = Conversation(
        speakers=_speakers,
        vlm_provider=self._settings.vlm_provider,
        image_qa_provider=self._settings.image_qa_provider,
        detection_provider=self._settings.detection_provider,
        reporter=self._reporter,
        cache_manager=cache_manager,
    )

    # Start conversation - providers are accessed internally by speakers
    conversation.start(
        messages=messages,
        on_message=on_message,
        tools=_tools,
        settings=_act_settings,
    )

def _build_speakers(self, caching_settings: CachingSettings | None) -> Speakers:
    """Build speakers collection based on caching settings."""
    from askui.speaker import AgentSpeaker, CacheExecutor, Speakers

    # AgentSpeaker accesses vlm_provider from conversation, no need to pass it here
    speakers_dict: dict[str, Speaker] = {
        "AgentSpeaker": AgentSpeaker(),
    }

    if caching_settings and caching_settings.strategy in ["read", "both"]:
        speakers_dict["CacheExecutor"] = CacheExecutor(
            execution_settings=caching_settings.execution_settings or CacheExecutionSettings()
        )

    return Speakers(speakers_dict)
```

#### Step 3.2: Deprecate old ActModel-based flow

The current `AskUIAgent` (ActModel) in `src/askui/models/shared/agent.py` should be removed as it is not needed anymore with the conversation-based architecture

### Phase 4: Update Tests

#### Step 4.1: Add unit tests for new components

```
tests/unit/speaker/
├── test_speaker.py
├── test_conversation.py
├── test_agent_speaker.py
└── test_cache_executor.py

tests/unit/utils/caching/
├── test_cache_manager.py
├── test_cache_parameter_handler.py
└── test_cache_validator.py
```

#### Step 4.2: Update existing tests

- Update `tests/unit/test_agent.py` for new `act()` signature
- Update `tests/e2e/agent/` tests for conversation-based flow

---

## 3. File Changes Summary

### New Files to Create

| File | Source | Notes |
|------|--------|-------|
| `src/askui/speaker/__init__.py` | New | Export public API |
| `src/askui/speaker/speaker.py` | Feature branch | Adapt default speaker name |
| `src/askui/speaker/conversation.py` | Feature branch | Minimal changes |
| `src/askui/speaker/agent_speaker.py` | Feature branch | Rename from `askui_agent.py`, add VlmProvider support |
| `src/askui/speaker/cache_executor.py` | Feature branch | Minimal changes |
| `src/askui/utils/caching/__init__.py` | New | Export public API |
| `src/askui/utils/caching/cache_manager.py` | Feature branch | Minimal changes |
| `src/askui/utils/caching/cache_parameter_handler.py` | Feature branch | Minimal changes |
| `src/askui/utils/caching/cache_validator.py` | Feature branch | New file |
| `src/askui/utils/visual_validation.py` | Feature branch | Direct copy |

### Files to Modify

| File | Changes |
|------|---------|
| `src/askui/agent_base.py` | Use Conversation, add speakers parameter |
| `src/askui/models/shared/settings.py` | Add CacheWritingSettings, CacheExecutionSettings, CacheMetadata, CacheFile |
| `src/askui/models/shared/agent_message_param.py` | Add `visual_representation` to ToolUseBlockParam |
| `src/askui/tools/caching_tools.py` | Update tools for new cache system |
| `src/askui/__init__.py` | Export new public classes |

### Files to Remove

| File | Action |
|------|--------|
| `src/askui/utils/cache_writer.py` | Remove (replaced by CacheManager) |
| `src/askui/models/shared/agent.py` | Remove |

---

## 4. Migration Notes

**No Backwards Compatibility -> we make a clean cut**

### 4.1 Breaking Changes

1. **CachingSettings structure changed:**
   - Old: `CachingSettings(strategy="write", filename="...")`
   - New: `CachingSettings(strategy="write", writing_settings=CacheWritingSettings(filename="..."))`

2. **Cache file format changed:**
   - Old: Plain list of ToolUseBlockParam
   - New: CacheFile with metadata, trajectory, and parameters

3. **New `speakers` parameter in `act()`:**
   - Optional, but enables custom speaker injection

### 4.3 Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing
    "imagehash>=4.3.0",  # For visual validation
]
```

---

## 5. Testing Strategy

### 5.1 Unit Tests (Priority: High)

1. `Speaker` ABC and `SpeakerResult` behavior
2. `Conversation` execution loop with mock speakers
3. `AgentSpeaker` LLM API integration
4. `CacheExecutor` step-by-step execution
5. `CacheManager` recording and playback
6. `CacheParameterHandler` parameter identification
7. `CacheValidator` validation strategies
8. Visual validation hash computation

### 5.2 Integration Tests (Priority: Medium)

1. Full `act()` flow with conversation
2. Cache recording and playback round-trip
3. Speaker switching during execution
4. Visual validation during cache execution

### 5.3 E2E Tests (Priority: Low)

1. Real agent execution with caching
2. Cache reuse across sessions
3. Parameter substitution in cached trajectories

---

## 6. Implementation Order

### Week 1: Foundation
1. Create speaker module structure
2. Implement `Speaker`, `SpeakerResult`, `Speakers`
3. Implement `Conversation` orchestrator
4. Add basic unit tests

### Week 2: Caching Infrastructure
1. Create caching utils structure
2. Implement `CacheManager`
3. Implement `CacheValidator`
4. Update settings with new cache types
5. Add visual validation utilities

### Week 3: Integration
1. Implement `AgentSpeaker` with VlmProvider support
2. Implement `CacheExecutor`
3. Update `Agent.act()` to use Conversation
4. Update caching tools

### Week 4: Testing & Polish
1. Comprehensive unit tests
2. Integration tests
3. Migration guide
4. Documentation updates
5. Deprecation warnings for old APIs

---

## 7. Open Questions

1. **Naming**: Should `AgentSpeaker` be named differently (e.g., `VlmSpeaker`, `LlmSpeaker`)? AgentSpeaker is fine as name

2. **Default speaker**: Should the default speaker be configurable at Agent level?

3. **Cache migration**: Should we auto-migrate old cache files or require manual migration? We do not migrate them

4. **Visual validation**: Should visual validation be opt-in or opt-out by default? It should be opt-out

5. **Provider options**: How should provider-specific options (like Anthropic betas) flow through the Conversation? this is part of the model providers. THey are passed to the conversation. apart of that we do not need to care for it

---

## 8. References

- Feature branch: `origin/feat/conversation_based_architecture`
- Key commits:
  - `47e124b feat: changes act logic to a novel converation-based format`
  - `7cb0f94 feat(caching): add visual validation and bump version to 0.2`
  - `d51c6d3 chore: run format`
