# Vision Agent Architecture

## Overview

The Vision Agent uses a **Conversation-based architecture** with a **Speaker pattern** to handle different types of agent interactions. This architecture separates concerns and allows for flexible conversation flows including normal API interactions and cached trajectory execution.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         VisionAgent                             │
│  (User-facing API: click, type, act, get, locate, etc.)         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ inherits from
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AgentBase                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ __init__:                                                │   │
│  │  • Creates Client (default: AskUIClient)                 │   │
│  │  • Creates Speakers (AskUIAgent, CacheExecutor)          │   │
│  │  • Creates Conversation with Speakers and Client         │   │
│  │  • Creates Default Models (for get/locate operations)    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ act():                                                   │   │
│  │  • Builds tools                                          │   │
│  │  • Sets up caching if needed                             │   │
│  │  • Resolves client (act() param > __init__ param)        │   │
│  │  • Calls self._conversation.start()                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ uses
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Conversation                               │
│  • Manages message history                                       │
│  • Stores and passes Client to speakers                          │
│  • Orchestrates speaker switching                                │
│  • Tracks accumulated token usage                                │
│  • Handles truncation strategy                                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ delegates to
                  ▼
    ┌─────────────────────────────┐
    │        Speakers              │
    │   (Speaker Pattern)          │
    └─────────────┬────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
        ▼                    ▼
┌──────────────┐    ┌────────────────┐
│ AskUIAgent   │    │ CacheExecutor  │
│  Speaker     │    │   Speaker      │
└──────────────┘    └────────────────┘
```

## Core Components

### 1. Conversation

**Location**: `src/askui/speaker/conversation.py`

The `Conversation` class is the central orchestrator that manages:
- **Message History**: List of MessageParam (user/assistant messages)
- **Speaker Management**: Dictionary of available speakers and current active speaker
- **Execution Loop**: Loop-based execution that switches between speakers
- **Token Usage**: Accumulates usage statistics across all speakers
- **Truncation**: Applies truncation strategy to message history
- **Reporters**: List of reporters set when conversation starts
- **Message Callback**: Optional callback for recording or intercepting messages (e.g., CacheManager.add_message_cb)

```python
class Conversation:
    speakers: dict[str, Speaker]
    current_speaker_name: str
    client: Client  # Client for LLM communication
    accumulated_usage: UsageParam
    _truncation_strategy: TruncationStrategy | None
    _on_message: OnMessageCb  # v0.1.1+
    _reporters: list[Reporter]  # v0.1.1+
```

**Flow**:
```
start() → _execute_loop() → while loop:
    1. Get current speaker
    2. Check if speaker can_handle()
    3. Call speaker.handle_step()
    4. Process SpeakerResult
    5. Switch speaker if needed
    6. Continue/Done/Failed
```

### 2. Speaker Pattern

**Base Class**: `src/askui/speaker/speaker.py`

All speakers implement the `Speaker` abstract base class:

```python
class Speaker(ABC):
    @abstractmethod
    def can_handle(self, conversation: Conversation) -> bool:
        """Check if this speaker can handle current state"""

    @abstractmethod
    def handle_step(
        self,
        conversation: Conversation,
        cache_manager: CacheManager | None,
        client: Client,
    ) -> SpeakerResult:
        """Execute one conversation step"""

    @abstractmethod
    def get_name(self) -> str:
        """Return speaker name"""
```

**SpeakerResult** indicates what to do next:
- `status="continue"`: Keep executing with same speaker
- `status="switch_speaker"`: Switch to different speaker
- `status="done"`: Conversation completed successfully
- `status="failed"`: Conversation failed

## Speakers

### AskUIAgent Speaker

**Location**: `src/askui/speaker/askui_agent.py`

Handles normal agent API interactions with LLM.

```
┌──────────────────────────────────────────────────────────┐
│                    AskUIAgent                             │
├──────────────────────────────────────────────────────────┤
│  Dependencies:                                            │
│    • Client (provided via handle_step parameter)         │
│    • Reporter                                             │
├──────────────────────────────────────────────────────────┤
│  Responsibilities:                                        │
│    1. Make API calls to LLM via client                   │
│    2. Handle stop reasons (max_tokens, refusal)          │
│    3. Return assistant responses                         │
│    4. Continue until conversation is complete            │
├──────────────────────────────────────────────────────────┤
│  can_handle(): Always returns True (default speaker)     │
├──────────────────────────────────────────────────────────┤
│  handle_step(conversation, cache_manager, client):       │
│    IF last message is user:                              │
│      • Use client.send_message() to get response         │
│      • Add assistant response                            │
│    • Check stop_reason                                   │
│    IF conversation should continue:                      │
│      → status="continue"                                 │
│    ELSE:                                                 │
│      → status="done" (conversation complete)             │
└──────────────────────────────────────────────────────────┘
```

### CacheExecutor Speaker

**Location**: `src/askui/speaker/cache_executor.py`

Handles cached trajectory execution (v0.1.1: merged execution logic from TrajectoryExecutor).

```
┌──────────────────────────────────────────────────────────┐
│                   CacheExecutor (v0.1.1)                  │
├──────────────────────────────────────────────────────────┤
│  Dependencies:                                            │
│    • CacheManager (for metadata updates & reading)       │
│    • ToolCollection (for executing cached tools)         │
│    • Reporter                                             │
├──────────────────────────────────────────────────────────┤
│  State (owned by speaker):                                │
│    • _executing_from_cache: bool                         │
│    • _cache_verification_pending: bool                   │
│    • _cache_file: CacheFile | None                       │
│    • _cache_file_path: str | None                        │
│    • _trajectory: list[ToolUseBlockParam]                │
│    • _toolbox: ToolCollection                            │
│    • _parameter_values: dict[str, str]                   │
│    • _current_step_index: int                            │
│    • _message_history: list[MessageParam]                │
├──────────────────────────────────────────────────────────┤
│  Responsibilities:                                        │
│    1. Execute steps from cached trajectories             │
│    2. Substitute parameters into tool inputs             │
│    3. Handle successful steps                            │
│    4. Pause for non-cacheable tools                      │
│    5. Request verification on completion                 │
│    6. Update metadata via CacheManager                   │
│    7. Manage execution state and delays                  │
├──────────────────────────────────────────────────────────┤
│  can_handle():                                            │
│    Returns _executing_from_cache                         │
├──────────────────────────────────────────────────────────┤
│  handle_step():                                           │
│    • Execute next step from cache (_execute_next_step)   │
│    • Handle result based on status:                      │
│      - SUCCESS: Add messages, continue                   │
│      - NEEDS_AGENT: Switch to askui_agent               │
│      - COMPLETED: Request verification                   │
│      - FAILED: Update metadata, switch to agent          │
├──────────────────────────────────────────────────────────┤
│  Internal Methods (v0.1.1 - merged from TrajectoryExecutor):│
│    • _execute_next_step(): Execute one trajectory step   │
│    • _should_pause_for_agent(): Check if tool cacheable  │
│    • _should_skip_step(): Check if step should be skipped│
│    • _validate_step_visually(): Visual validation hook   │
└──────────────────────────────────────────────────────────┘
```

## Client Interface for LLM Communication

### Client Interface

**Location**: `src/askui/models/shared/messages_api.py`

The `Client` is the interface for making API calls to LLM providers. Users can provide custom implementations to use different LLM backends.

```
┌──────────────────────────────────────────────────────────┐
│                    Client (ABC)                           │
├──────────────────────────────────────────────────────────┤
│  Abstract interface for LLM API interactions              │
├──────────────────────────────────────────────────────────┤
│  @abstractmethod                                          │
│  def send_message(                                        │
│      messages: list[MessageParam],                       │
│      model: str,                                          │
│      system: str | list[BetaTextBlockParam],             │
│      tools: ToolCollection,                              │
│      max_tokens: int,                                     │
│      ...                                                  │
│  ) -> MessageParam                                        │
├──────────────────────────────────────────────────────────┤
│  Implementations:                                         │
│    • AskUIClient - Default client using Anthropic API    │
│    • AnthropicClient - Direct Anthropic API access       │
│    • Custom clients - User-provided implementations      │
└──────────────────────────────────────────────────────────┘
```

**Key responsibilities:**
- Send messages to LLM and receive responses
- Handle authentication
- Return standardized `MessageParam` responses
- Manage API-specific features

### AskUIClient

**Location**: `src/askui/models/askui_client.py`

Default client implementation that uses the Anthropic API via AskUI infrastructure.

```
┌──────────────────────────────────────────────────────────┐
│                    AskUIClient                            │
├──────────────────────────────────────────────────────────┤
│  Default client for VisionAgent                          │
├──────────────────────────────────────────────────────────┤
│  State:                                                   │
│    • _anthropic_client: AnthropicClient                  │
│    • _api_provider: AnthropicApiProvider                 │
│    • _locator_serializer: VlmLocatorSerializer           │
├──────────────────────────────────────────────────────────┤
│  Methods:                                                 │
│    • send_message(...) -> MessageParam                   │
│      Delegates to AnthropicClient                        │
└──────────────────────────────────────────────────────────┘
```

**Usage:**
```python
# Default usage (automatically created if no client provided)
agent = VisionAgent()
agent.act("Do something")

# Explicit client at initialization
client = AskUIClient()
agent = VisionAgent(client=client)

# Client provided to act() (takes priority)
agent.act("Do something", client=custom_client)
```

### Default Models (Simplified Architecture)

**Locations**:
- `src/askui/models/askui/models.py` - AskUI model implementations
- `src/askui/agent_base.py` - Model initialization

Handles `get` and `locate` operations using default AskUI models (act uses Conversation + Client architecture).

```
┌──────────────────────────────────────────────────────────┐
│                  Default Models                           │
├──────────────────────────────────────────────────────────┤
│  Models Initialized in AgentBase:                        │
│    • _default_get_model: AskUiGetModel (via ModelFacade) │
│    • _default_locate_model: AskUiLocateModel             │
├──────────────────────────────────────────────────────────┤
│  Get Model (AskUiGetModel):                              │
│    • get(query, source, response_schema, model)          │
│      → Extract data from images/screenshots              │
│    • Uses AskUiGoogleGenAiApi and AskUiInferenceApi      │
├──────────────────────────────────────────────────────────┤
│  Locate Model (AskUiLocateModel):                        │
│    • locate(locator, image, model)                       │
│      → Find UI elements in screenshots                   │
│    • locate_all_elements(image, model)                   │
│      → Find all interactive elements                     │
│    • Uses AskUiInferenceApi with AskUiLocatorSerializer  │
└──────────────────────────────────────────────────────────┘
```

**Initialization:**
```python
# In AgentBase._init_default_models()
def _init_default_models(self, reporter: Reporter) -> tuple[GetModel, LocateModel]:
    """Initialize default get and locate models."""
    inference_api = AskUiInferenceApi(settings=AskUiInferenceApiSettings())

    # Initialize locate model
    locate_model = AskUiLocateModel(
        locator_serializer=AskUiLocatorSerializer(...),
        inference_api=inference_api,
    )

    # Initialize get model
    get_model = ModelFacade(
        act_model=None,
        get_model=AskUiGetModel(...),
        locate_model=locate_model,
    )

    return get_model, locate_model
```

**Usage:**
```python
# In VisionAgent.get() - uses _default_get_model
_source = source or ImageSource(self._agent_os.screenshot())
return self._data_extractor.get(
    query=query,
    source=_source,
    model=_model,
    response_schema=response_schema,
)

# In VisionAgent.locate() - uses _default_locate_model
_model = model or self._get_model(None, "locate")
return self._default_locate_model.locate(
    locator=locator,
    image=_screenshot,
    model=_model,
)
```

## Caching Architecture (v0.1.1)

### Overview

The caching system allows recording and replaying agent trajectories (sequences of actions).

**Version**: v0.1.1 (TrajectoryExecutor merged into CacheExecutor, CacheWriter managed by Conversation)

```
┌─────────────────────────────────────────────────────────────────┐
│                 Caching Architecture (v0.1.1)                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐
│  Cache Writer   │    │  Cache Manager   │    │ Cache Executor │
│                 │    │                  │    │   Speaker      │
│  Records agent  │    │  Reads & writes  │    │  Executes from │
│  trajectories   │    │  cache files     │    │  cache         │
│  (member of     │    │  Validates &     │    │  (includes     │
│  Conversation)  │    │  manages metadata│    │  execution     │
│                 │    │                  │    │  logic)        │
└─────────────────┘    └──────────────────┘    └────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Cache Files                               │
│  JSON files containing:                                          │
│    • Trajectory steps (tool calls and results)                   │
│    • Parameters (variables that can differ)                      │
│    • Metadata (success count, last used, etc.)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Caching Components

#### 1. CacheWriter (v0.1.1)

**Location**: `src/askui/utils/caching/cache_writer.py`

- **Member of Conversation** - Initialized in `Conversation.start()` when caching is enabled
- Records agent actions during execution via on_message callback
- Creates trajectory files in cache directory
- Parameterizes variable values (e.g., passwords, usernames)
- **Responsibility**: Write-only (reading moved to CacheManager in v0.1.1)

#### 2. CacheManager (v0.1.1)

**Location**: `src/askui/utils/caching/cache_manager.py`

- Reads cache files from disk (`read_cache_file()` - moved from CacheWriter in v0.1.1)
- Manages cache metadata and validation
- Records execution attempts and failures
- Validates caches using pluggable validation strategies
- Invalidates caches when they fail validation
- Updates metadata files on disk

```python
class CacheManager:
    validators: CompositeCacheValidator

    @staticmethod
    def read_cache_file(cache_file_path) -> CacheFile  # v0.1.1+

    def record_execution_attempt(cache_file, success, failure_info)
    def record_step_failure(cache_file, step_index, error_message)
    def should_invalidate(cache_file, step_index) -> tuple[bool, str]
    def invalidate_cache(cache_file, reason)
    def mark_cache_valid(cache_file)  # v0.1.1+
    def get_failure_count_for_step(cache_file, step_index)  # v0.1.1+
    def update_metadata_on_failure(cache_file, cache_file_path, ...)
    def update_metadata_on_completion(cache_file, cache_file_path, ...)
```

#### 3. CacheManager Recording (v0.1.1)

**Note**: In v0.1.1, CacheWriter was merged into CacheManager. CacheManager now handles both reading and writing cache files.

CacheManager includes recording functionality (formerly CacheWriter) for write mode:

```
┌──────────────────────────────────────────────────────────┐
│           CacheManager Recording (v0.1.1)                │
├──────────────────────────────────────────────────────────┤
│  Lifecycle:                                               │
│    • Created by AgentBase when strategy = "write"/"both" │
│    • start_recording() called to initialize state        │
│    • Conversation executes normally                      │
│    • finish_recording(messages) extracts tool blocks     │
│      from message history and writes cache file          │
├──────────────────────────────────────────────────────────┤
│  Recording State:                                         │
│    • _recording: bool                                     │
│    • _tool_blocks: list[ToolUseBlockParam]               │
│    • _cache_dir: Path | None                             │
│    • _file_name: str                                      │
│    • _was_cached_execution: bool                         │
│    • _accumulated_usage: UsageParam                      │
│    • _toolbox: ToolCollection | None                     │
│    • _goal: str | None                                   │
├──────────────────────────────────────────────────────────┤
│  Recording Methods:                                       │
│    • start_recording(): Initialize recording state       │
│    • finish_recording(messages): Extract tool blocks     │
│      from messages and write cache file                  │
│    • _extract_from_messages(): Extract tool blocks       │
│    • _reset_recording_state(): Clear recording state     │
│    • _parameterize_trajectory(): Identify cache params   │
│    • _blank_non_cacheable_tool_inputs(): Privacy/space   │
│    • _generate_cache_file(): Write JSON with v0.1.1      │
│    • _accumulate_usage(): Track token usage              │
└──────────────────────────────────────────────────────────┘
```

**Integration with Conversation:**
```python
# In AgentBase._patch_act_with_cache()
cache_manager = CacheManager()
cache_manager.start_recording(
    cache_dir=".cache",
    file_name="test.json",
    goal=goal,
    toolbox=toolbox,
    cache_writer_settings=settings
)
return cache_manager

# In AgentBase.act()
self._conversation.start(
    messages=messages,
    model=model,
    on_message=on_message,
    settings=settings,
    tools=tools,
)

# After conversation completes
if cache_manager is not None:
    cache_manager.finish_recording(self._conversation.get_messages())
    # Extracts tool blocks from message history and writes cache file
```

#### 4. Cache Validators

**Location**: `src/askui/utils/caching/cache_validator.py`

Pluggable validation strategies for cache invalidation:
- **StepFailureCountValidator**: Invalidates if a step fails too many times
- **TotalFailureRateValidator**: Invalidates if overall failure rate is too high
- **StaleCacheValidator**: Invalidates if cache is too old
- **CompositeCacheValidator**: Combines multiple validators

### Caching Tools

#### ExecuteCachedTrajectory (v0.1.1)

**Location**: `src/askui/tools/caching_tools.py`

Tool that the agent can call to execute a cached trajectory:

```python
def __call__(
    trajectory_file: str,
    parameter_values: dict[str, str]
) -> str:
    # 1. Load cache file via CacheManager.read_cache_file()
    # 2. Activate cache execution via CacheExecutor speaker
    #    (passes trajectory data directly, no TrajectoryExecutor)
    # 3. Return confirmation message
```

#### VerifyCacheExecution

Tool that the agent uses to verify if cache execution achieved the goal:

```python
def __call__(
    verification_result: Literal["success", "failure"],
    reason: str
) -> str:
    # 1. Update cache metadata
    # 2. Reset cache state
    # 3. Return result message
```

#### RetrieveCachedTestExecutions

Tool that retrieves available cached trajectories:

```python
def __call__() -> str:
    # 1. Scan cache directory
    # 2. Find matching trajectories
    # 3. Return list of available caches
```

## Execution Flow Examples

### Normal Act Execution

```
1. User calls: agent.act("Open settings")
   │
   ▼
2. AgentBase.act()
   • Builds tools
   • Sets up caching if needed
   • Resolves client (act param > init param > default)
   • Calls conversation.start()
   │
   ▼
3. Conversation.start()
   • Initializes with user message
   • Stores client
   • Starts _execute_loop()
   │
   ▼
4. Loop iteration:
   │
   ├─▶ AskUIAgent.can_handle() → True
   │
   ├─▶ AskUIAgent.handle_step(conversation, cache_manager, client)
   │   • Uses client.send_message() to call LLM
   │   • Gets assistant response
   │   • Returns SpeakerResult(status="continue" or "done")
   │
   ├─▶ Process result
   │   • Add messages to history
   │   • Update usage stats
   │   • Execute any tools in response
   │   • Continue if status="continue"
   │   • Exit if status="done"
   │
   └─▶ Repeat until done
```

### Cached Execution Flow

```
1. Agent receives goal with caching enabled
   │
   ▼
2. Agent has caching tools available:
   • RetrieveCachedTestExecutions
   • ExecuteCachedTrajectory
   • VerifyCacheExecution
   │
   ▼
3. Agent calls RetrieveCachedTestExecutions
   • Finds matching cached trajectory
   │
   ▼
4. Agent calls ExecuteCachedTrajectory (v0.1.1)
   • CacheExecutor.activate_cache_execution()
   • Receives trajectory data, toolbox, parameters directly
   • Sets _executing_from_cache = True
   │
   ▼
5. Conversation loop switches to CacheExecutor:
   │
   ├─▶ CacheExecutor.can_handle() → True
   │   (because _executing_from_cache = True)
   │
   ├─▶ CacheExecutor.handle_step()
   │   • Calls _execute_next_step() internally
   │   • Executes cached tools with parameter substitution
   │   • Returns result based on execution status
   │
   ├─▶ Status handling:
   │   │
   │   ├─ SUCCESS: Add messages, continue
   │   │
   │   ├─ NEEDS_AGENT: Switch to AskUIAgent
   │   │  (for non-cacheable tools)
   │   │
   │   ├─ COMPLETED: Request verification
   │   │  • Inject verification request message
   │   │  • Switch to AskUIAgent
   │   │
   │   └─ FAILED: Update metadata, switch to agent
   │
   └─▶ Repeat until completed or failed
   │
   ▼
6. Agent verifies cache execution
   • Calls VerifyCacheExecution tool
   • Updates metadata (success count, etc.)
   • Resets cache state
```

## Message Flow

```
┌──────────────────────────────────────────────────────────────┐
│                     Message Types                             │
└──────────────────────────────────────────────────────────────┘

MessageParam (role="user"):
  • User instructions
  • Tool results
  • Cache verification requests

MessageParam (role="assistant"):
  • LLM responses
  • Tool use blocks
  • Text responses

Content Blocks:
  • TextBlockParam: Text content
  • ToolUseBlockParam: Tool invocation
  • ToolResultBlockParam: Tool execution result
  • ImageBlockParam: Image data
```

## Truncation Strategy

**Location**: `src/askui/models/shared/truncation_strategies.py`

Manages message history to fit within context limits:

```
┌──────────────────────────────────────────────────────────┐
│             TruncationStrategy                            │
├──────────────────────────────────────────────────────────┤
│  SimpleTruncationStrategy:                               │
│    • Keeps first message (usually system/instruction)    │
│    • Keeps recent messages up to token limit             │
│    • Drops middle messages if needed                     │
├──────────────────────────────────────────────────────────┤
│  Used by Conversation to truncate message history        │
│  before sending to LLM                                    │
└──────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Separation of Concerns
- **Conversation**: Message management and orchestration
- **Speakers**: Specific execution logic
- **Models**: API interactions and data models

### 2. Speaker Pattern Benefits
- Easy to add new speakers (e.g., HumanInTheLoop)
- Clear state transitions via SpeakerResult
- Each speaker focused on single responsibility

### 3. Loop-Based Execution
- No recursion (avoids stack overflow)
- Clear control flow
- Easy to debug and trace

### 4. Client-Based LLM Communication
- Client interface provides clean abstraction for LLM communication
- Users can provide custom clients for different LLM backends
- Client resolution happens once at beginning of act() for performance
- Client flows through: AgentBase → Conversation → Speaker.handle_step()

### 5. Caching Integration
- Seamless integration via speaker pattern
- Cache execution is just another conversation flow
- Agent can transparently switch between live and cached execution

## File Structure

```
src/askui/
├── speaker/
│   ├── __init__.py
│   ├── speaker.py              # Speaker ABC and SpeakerResult
│   ├── conversation.py         # Conversation orchestrator
│   ├── askui_agent.py          # AskUI Agent speaker
│   └── cache_executor.py       # Cache Executor speaker
│
├── models/
│   ├── askui_client.py          # Default Client implementation
│   │
│   ├── anthropic/
│   │   ├── messages_api.py           # Anthropic Client implementation
│   │   └── factory.py                # API client creation
│   │
│   ├── shared/
│   │   ├── messages_api.py           # Client interface (ABC)
│   │   ├── agent_message_param.py    # Message types
│   │   ├── agent_on_message_cb.py    # Callback types
│   │   ├── settings.py               # Settings models
│   │   ├── tools.py                  # Tool definitions
│   │   ├── truncation_strategies.py  # Message truncation
│   │   └── facade.py                 # Model facade
│   │
│   └── askui/
│       ├── models.py                 # AskUI model implementations (GetModel, LocateModel)
│       ├── inference_api.py          # AskUI inference API
│       └── google_genai_api.py       # Google GenAI API integration
│
├── utils/
│   └── caching/
│       ├── cache_writer.py               # Records trajectories (write-only)
│       ├── cache_manager.py              # Reads cache files, manages metadata & validation
│       ├── cache_validator.py            # Validation strategies
│       └── cache_parameter_handler.py    # Parameter substitution
│
├── tools/
│   └── caching_tools.py        # Caching tools for agent
│
├── agent_base.py               # Base agent class
├── agent.py                    # VisionAgent (user API)
└── custom_agent.py             # CustomAgent (simpler API)
```

## Future Extensions

The architecture is designed to be extensible:

### Potential New Speakers
- **HumanInTheLoopSpeaker**: Pause for human input
- **ValidationSpeaker**: Validate agent actions
- **RetryStrategySpeaker**: Handle retries with backoff
- **MultiModalSpeaker**: Handle vision + audio

### Caching Enhancements
- Cache sharing across users
- Cloud-based cache storage
- Cache invalidation strategies
- Automatic cache updates

### Model Routing
- Model selection based on task type
- Cost optimization (use cheaper models)
- Fallback models on failure
- Multi-model ensembles
