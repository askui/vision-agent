# Caching (Experimental)

**Version: v0.1.1** - Improved architecture with simplified components and better separation of concerns.

**CAUTION: The Caching feature is still in alpha state and subject to change! Use it at your own risk. In case you run into issues, you can disable caching by removing the caching_settings parameter or by explicitly setting the caching_strategy to `no`.**

The caching mechanism allows you to record and replay agent action sequences (trajectories) for faster and more robust test execution. This feature is particularly useful for regression testing, where you want to replay known-good interaction sequences to verify that your application still behaves correctly.

## Overview

The caching system works by recording all tool use actions (mouse movements, clicks, typing, etc.) performed by the agent during an `act()` execution. These recorded sequences can then be replayed in subsequent executions, allowing the agent to skip the decision-making process and execute the actions directly.

**New in v0.1:** The caching system now includes advanced features like parameter support for dynamic values, smart handling of non-cacheable tools that require agent intervention, comprehensive message history tracking, and automatic failure detection with recovery capabilities.

**New in v0.1.1:**
- Simplified architecture: TrajectoryExecutor merged into CacheExecutor speaker for better encapsulation
- CacheWriter merged into CacheManager - single class now handles all cache file operations (read, write, update)
- Cache recording simplified: finish_recording() extracts tool blocks from message history instead of using callbacks
- Cleaner separation of concerns with fewer abstraction layers

## Caching Strategies

The caching mechanism supports four strategies, configured via the `caching_settings` parameter in the `act()` method:

- **`None`** (default): No caching is used. The agent executes normally without recording or replaying actions.
- **`"record"`**: Records all agent actions to a cache file for future replay.
- **`"execute"`**: Provides tools to the agent to list and execute previously cached trajectories.
- **`"both"`**: Combines execute and record modes - the agent can use existing cached trajectories and will also record new ones.

## Configuration

Caching is configured using the `CachingSettings` class:

```python
from askui.models.shared.settings import CachingSettings, CacheExecutionSettings, CacheWritingSettings

caching_settings = CachingSettings(
    strategy="write",        # One of: "execute", "record", "both", or None
    cache_dir=".cache",      # Directory to store cache files
    writing_settings=CacheWritingSettings(
        filename="my_test.json",  # Filename for the cache file (required for write mode)
        parameter_identification_strategy="llm",  # Auto-detect dynamic values (default: "llm")
        visual_verification_method="phash",  # Visual validation method (default: "phash")
    ),
    execution_settings=CacheExecutionSettings(
        delay_time_between_action=0.5  # Delay in seconds between each cached action
    )
)
```

### Parameters

- **`strategy`**: The caching strategy to use (`"execute"`, `"record"`, `"both"`, or `None`).
- **`cache_dir`**: Directory where cache files are stored. Defaults to `".askui_cache"`.
- **`writing_settings`**: Configuration for cache recording when using `"record"` or `"both"` strategy. See [Cache Writing Settings](#cache-writing-settings) below.
- **`execution_settings`**: Configuration for the trajectory execution when using `"execute"` or `"both"` strategy. See [Cache Execution Settings](#cache-execution-settings) below.

### Cache Writing Settings

The `CacheWritingSettings` class allows you to configure how cache files are recorded:

```python
from askui.models.shared.settings import CacheWritingSettings

writing_settings = CacheWritingSettings(
    filename="my_test.json",  # Filename for the cache file
    parameter_identification_strategy="llm",  # Auto-detect dynamic values (default: "llm")
    visual_verification_method="phash",  # Visual validation method (default: "phash")
    visual_validation_region_size=100,  # Region size for visual validation (default: 100)
    visual_validation_threshold=10,  # Threshold for visual validation (default: 10)
)
```

#### Parameters

- **`filename`**: Name of the cache file to write to. If not specified, a timestamped filename will be generated automatically (format: `cached_trajectory_YYYYMMDDHHMMSSffffff.json`). Defaults to `""`.
- **`parameter_identification_strategy`**: When `llm` (default), uses AI to automatically identify and parameterize dynamic values like dates, usernames, and IDs during cache recording. When `preset`, only manually specified cache_parameters (using `{{...}}` syntax) are detected. See [Automatic Cache Parameter Identification](#automatic-parameter-identification).
- **`visual_verification_method`**: The method used for visual validation. Options: `"phash"` (perceptual hash), `"ahash"` (average hash), or `"none"` (no validation). Defaults to `"phash"`.
- **`visual_validation_region_size`**: The size of the region used for visual validation. Defaults to `100`.
- **`visual_validation_threshold`**: The threshold for visual validation. Defaults to `10`.

### Cache Execution Settings

The `CacheExecutionSettings` class allows you to configure how cached trajectories are executed:

```python
from askui.models.shared.settings import CacheExecutionSettings

execution_settings = CacheExecutionSettings(
    delay_time_between_action=0.5  # Delay in seconds between each action (default: 0.5)
)
```

#### Parameters

- **`delay_time_between_action`**: The time to wait (in seconds) between executing consecutive cached actions. This delay helps ensure UI elements have time to respond before the next action is executed. Defaults to `0.5` seconds.

You can adjust this value based on your application's responsiveness:
- For faster applications or quick interactions, you might use a smaller delay (e.g., `0.1` or `0.2` seconds)
- For slower applications or complex UI updates, you might need a longer delay (e.g., `1.0` or `2.0` seconds)

## Usage Examples

### Writing a Cache (Recording)

Record agent actions to a cache file for later replay:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

with VisionAgent() as agent:
    agent.act(
        goal="Fill out the login form with username 'admin' and password 'secret123'",
        caching_settings=CachingSettings(
            strategy="record",
            cache_dir=".cache",
            writing_settings=CacheWritingSettings(
                filename="login_test.json"
            )
        )
    )
```

After execution, a cache file will be created at `.cache/login_test.json` containing all the tool use actions performed by the agent, along with metadata about the execution.

### Reading from Cache (Replaying)

Provide the agent with access to previously recorded trajectories:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

with VisionAgent() as agent:
    agent.act(
        goal="Fill out the login form",
        caching_settings=CachingSettings(
            strategy="execute",
            cache_dir=".cache"
        )
    )
```

When using `strategy="execute"`, the agent receives two tools:

1. **`RetrieveCachedTestExecutions`**: Lists all available cache files in the cache directory
2. **`ExecuteCachedTrajectory`**: Executes a cached trajectory. Can start from the beginning (default) or continue from a specific step index using the optional `start_from_step_index` parameter (useful after handling non-cacheable steps)

The agent will automatically check if a relevant cached trajectory exists and use it if appropriate. During execution, the agent can see all screenshots and results in the message history. After executing a cached trajectory, the agent will verify the results and make corrections if needed.

### Using Cache Parameters for Dynamic Values

**New in v0.1:** Trajectories can contain cache_parameters for dynamic values that change between executions:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

# When recording, use dynamic values as normal
# The system automatically detects patterns like dates and user-specific data
with VisionAgent() as agent:
    agent.act(
        goal="Create a new task for today with the title 'Review PR'",
        caching_settings=CachingSettings(
            strategy="record",
            cache_dir=".cache",
            writing_settings=CacheWritingSettings(
                filename="create_task.json"
            )
        )
    )

# Later, when replaying, the agent can provide parameter values
# If the cache file contains {{current_date}} or {{task_title}}, provide them:
with VisionAgent() as agent:
    agent.act(
        goal="Create a task using the cached flow",
        caching_settings=CachingSettings(
            strategy="execute",
            cache_dir=".cache"
        )
    )
    # The agent will automatically detect required cache_parameters and can provide them
    # via the parameter_values parameter when calling ExecuteCachedTrajectory
```

Cache Parameters use the syntax `{{variable_name}}` and are automatically detected during cache file creation. When executing a trajectory with cache_parameters, the agent must provide values for all required cache_parameters.

### Handling Non-Cacheable Steps

**New in v0.1:** Some tools cannot be cached and require the agent to execute them live. Examples include debugging tools, contextual decisions, or tools that depend on runtime state.

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

with VisionAgent() as agent:
    agent.act(
        goal="Debug the login form by checking element states",
        caching_settings=CachingSettings(
            strategy="execute",
            cache_dir=".cache"
        )
    )
    # If the cached trajectory contains non-cacheable steps:
    # 1. Execution pauses when reaching the non-cacheable step
    # 2. Agent receives NEEDS_AGENT status with current step index
    # 3. Agent executes the non-cacheable step manually
    # 4. Agent uses ExecuteCachedTrajectory with start_from_step_index to resume
```

Tools can be marked as non-cacheable by setting `is_cacheable=False` in their definition. When trajectory execution reaches a non-cacheable tool, it pauses and returns control to the agent for manual execution.

### Continuing from a Specific Step

**New in v0.1:** After handling a non-cacheable step or recovering from a failure, the agent can continue execution from a specific step index using the `start_from_step_index` parameter:

```python
# The agent uses ExecuteCachedTrajectory with start_from_step_index like this:
result = execute_cached_trajectory_tool(
    trajectory_file=".cache/my_test.json",
    start_from_step_index=5,  # Continue from step 5
    parameter_values={"date": "2025-12-11"}  # Provide any required cache_parameters
)
```

This is particularly useful for:
- Resuming after manual execution of non-cacheable steps
- Recovering from partial failures
- Skipping steps that are no longer needed

### Referencing Cache Files in Goal Prompts

When using `strategy="execute"` or `strategy="both"`, you need to inform the agent about which cache files are available and when to use them. This is done by including cache file information directly in your goal prompt.

#### Explicit Cache File References

For specific tasks, mention the cache file name and what it accomplishes:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

with VisionAgent() as agent:
    agent.act(
        goal="""Open the website in Google Chrome.

        If the cache file "open_website_in_chrome.json" is available, please use it
        for this execution. It will open a new window in Chrome and navigate to the website.""",
        caching_settings=CachingSettings(
            strategy="execute",
            cache_dir=".cache"
        )
    )
```

#### Pattern-Based Cache File References

For test suites or repetitive workflows, you can establish naming conventions:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

test_id = "TEST_001"

with VisionAgent() as agent:
    agent.act(
        goal=f"""Execute test {test_id} according to the test definition.

        Check if a cache file named "{test_id}.json" exists. If it does, use it to
        replay the test actions, then verify the results.""",
        caching_settings=CachingSettings(
            strategy="execute",
            cache_dir="test_cache"
        )
    )
```

#### General Rules for Cache Selection

You can also provide general instructions for the agent to identify applicable cache files:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

with VisionAgent() as agent:
    agent.act(
        goal="""Fill out the user registration form.

        Look for cache files that match the pattern "user_registration_*.json".
        Choose the most recent one if multiple are available, as it likely contains
        the most up-to-date interaction sequence.""",
        caching_settings=CachingSettings(
            strategy="execute",
            cache_dir=".cache"
        )
    )
```

#### Multiple Cache Files

For complex workflows, you can reference multiple cache files:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

with VisionAgent() as agent:
    agent.act(
        goal="""Complete the full checkout process:

        1. If "login.json" exists, use it to log in
        2. If "add_to_cart.json" exists, use it to add items to cart
        3. If "checkout.json" exists, use it to complete the checkout

        After each cached execution, verify the step completed successfully before proceeding.""",
        caching_settings=CachingSettings(
            strategy="execute",
            cache_dir=".cache"
        )
    )
```

**Best Practices:**
- Be specific about what the cache file does to help the agent decide if it's applicable
- Include verification instructions after cached execution
- Use consistent naming conventions for easier cache file management
- Mention any prerequisites or expected UI state for the cached trajectory

### Using Custom Execution Settings

You can customize the delay between cached actions to match your application's responsiveness:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings, CacheExecutionSettings

with VisionAgent() as agent:
    agent.act(
        goal="Fill out the login form",
        caching_settings=CachingSettings(
            strategy="execute",
            cache_dir=".cache",
            execution_settings=CacheExecutionSettings(
                delay_time_between_action=1.0  # Wait 1 second between each action
            )
        )
    )
```

This is particularly useful when:
- Your application has animations or transitions that need time to complete
- UI elements take time to become interactive after appearing
- You're testing on slower hardware or environments

### Using Both Strategies

Enable both reading and writing simultaneously:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

with VisionAgent() as agent:
    agent.act(
        goal="Complete the checkout process",
        caching_settings=CachingSettings(
            strategy="both",
            cache_dir=".cache",
            writing_settings=CacheWritingSettings(
                filename="checkout_test.json"
            )
        )
    )
```

In this mode:
- The agent can use existing cached trajectories to speed up execution
- New actions will be recorded to the specified cache file
- If a cached execution is used, no new cache file will be written (to avoid duplicates)

## Cache File Format

**New in v0.1:** Cache files now use an enhanced format with metadata tracking, parameter support, and execution history.

### v0.1 Format (Current)

Cache files are JSON objects with the following structure:

```json
{
  "metadata": {
    "version": "0.1",
    "created_at": "2025-12-11T10:30:00Z",
    "goal": "Greet user {{user_name}} and log them in",
    "last_executed_at": "2025-12-11T15:45:00Z",
    "execution_attempts": 3,
    "failures": [
      {
        "timestamp": "2025-12-11T14:20:00Z",
        "step_index": 5,
        "error_message": "Element not found",
        "failure_count_at_step": 1
      }
    ],
    "is_valid": true,
    "invalidation_reason": null
  },
  "trajectory": [
    {
      "type": "tool_use",
      "id": "toolu_01AbCdEfGhIjKlMnOpQrStUv",
      "name": "computer",
      "input": {
        "action": "type",
        "text": "Hello {{user_name}}!"
      }
    },
    {
      "type": "tool_use",
      "id": "toolu_02XyZaBcDeFgHiJkLmNoPqRs",
      "name": "print_debug_info",
      "input": {}
    }
  ],
  "cache_parameters": {
    "user_name": "Name of the user to greet"
  }
}
```

**Note:** In the example above, `print_debug_info` is marked as non-cacheable (`is_cacheable=False`), so its `input` field is blank (`{}`). This saves space and privacy since non-cacheable tools aren't executed from cache anyway.

#### Metadata Fields

- **`version`**: Cache file format version (currently "0.1")
- **`created_at`**: ISO 8601 timestamp when the cache was created
- **`goal`**: **New!** The original goal/instruction given to the agent when recording this trajectory. Cache Parameters are applied to the goal text just like in the trajectory, making it easy to understand what the cache was designed to accomplish.
- **`last_executed_at`**: ISO 8601 timestamp of the last execution (null if never executed)
- **`execution_attempts`**: Number of times this trajectory has been executed
- **`failures`**: List of failures encountered during execution (see [Failure Tracking](#failure-tracking))
- **`is_valid`**: Boolean indicating if the cache is still considered valid
- **`invalidation_reason`**: Optional string explaining why the cache was invalidated

#### Cache Parameters

The `cache_parameters` object maps parameter names to their descriptions. Cache Parameters in the trajectory use the syntax `{{parameter_name}}` and must be substituted with actual values during execution.

#### Failure Tracking

Each failure record contains:
- **`timestamp`**: When the failure occurred
- **`step_index`**: Which step failed (0-indexed)
- **`error_message`**: The error that occurred
- **`failure_count_at_step`**: How many times this specific step has failed

This information helps with cache invalidation decisions and debugging.

### v0.0 Format (Legacy)

The old format was a simple JSON array:

```json
[
  {
    "type": "tool_use",
    "id": "toolu_01AbCdEfGhIjKlMnOpQrStUv",
    "name": "computer",
    "input": {
      "action": "mouse_move",
      "coordinate": [150, 200]
    }
  }
]
```

**Backward Compatibility:** v0.0 cache files are automatically migrated to v0.1 format when read. The system adds default metadata and wraps the trajectory array in the new structure. This migration is transparent and requires no user intervention.

## How It Works

### Internal Architecture (v0.1.1)

The caching system consists of two key components:

1. **`CacheManager`** (Utility)
   - **v0.1.1**: Now handles both reading and writing cache files (CacheWriter merged in)
   - Recording methods: start_recording(), add_message_cb(), finish_recording()
   - Records agent actions via on_message callback
   - Handles trajectory recording and parameterization
   - Manages cache metadata operations
   - Validates caches using pluggable validation strategies
   - Handles invalidation logic and failure tracking

2. **`CacheExecutor`** (Speaker)
   - Manages cache execution state and orchestrates trajectory replay
   - **v0.1.1**: Now includes execution logic (merged from TrajectoryExecutor)
   - Executes cached steps directly with parameter substitution
   - Handles delays, non-cacheable tools, and agent switching
   - Owns all execution state (trajectory, toolbox, step index, etc.)

**Key Changes in v0.1.1:**
- TrajectoryExecutor eliminated - logic merged into CacheExecutor speaker
- CacheWriter eliminated - recording logic merged into CacheManager
- CacheManager is now the single source of truth for all cache file operations
- Cleaner, more cohesive architecture with fewer abstraction layers

This separation of concerns ensures:
- CacheExecutor is a self-contained execution speaker (no delegation needed)
- CacheManager centralizes all file I/O, metadata, and recording logic
- Single instance manages entire cache lifecycle

### Write Mode

In write mode, the `CacheManager` recording functionality:

1. Intercepts all assistant messages via a callback function
2. Extracts tool use blocks from the messages
3. Stores tool blocks in memory during execution
4. When agent finishes (on `stop_reason="end_turn"`):
   - **Automatically identifies cache_parameters** using AI (if `parameter_identification_strategy=llm`)
     - Analyzes trajectory to find dynamic values (dates, usernames, IDs, etc.)
     - Generates descriptive parameter definitions
     - Replaces identified values with `{{parameter_name}}` syntax in trajectory
     - Applies same replacements to the goal text
   - **Blanks non-cacheable tool inputs** by setting `input: {}` for tools with `is_cacheable=False` (saves space and privacy)
   - **Writes to JSON file** with:
     - v0.1 metadata (version, timestamps, goal with cache_parameters)
     - Trajectory of tool use blocks (with cache_parameters and blanked inputs)
     - Parameter definitions with descriptions
5. Automatically skips writing if a cached execution was used (to avoid recording replays)

### Read Mode

In read mode:

1. Two caching tools are added to the agent's toolbox:
   - `RetrieveCachedTestExecutions`: Lists available trajectories
   - `ExecuteCachedTrajectory`: Executes from the beginning or continues from a specific step using `start_from_step_index`
2. A special system prompt (`CACHE_USE_PROMPT`) instructs the agent on:
   - How to use trajectories
   - Parameter handling
   - Non-cacheable step management
   - Failure recovery strategies
3. The agent can list available cache files and choose appropriate ones
4. During execution via `CacheExecutor` (v0.1.1):
   - CacheExecutor executes each step sequentially with configurable delays
   - All tools in the trajectory are executed, including screenshots and retrieval tools
   - Non-cacheable tools trigger a pause with `NEEDS_AGENT` status
   - Cache Parameters are validated and substituted before execution
   - Message history is built with assistant (tool use) and user (tool result) messages
   - Agent sees all screenshots and results in the message history
5. Execution can pause for agent intervention:
   - When reaching non-cacheable tools
   - When errors occur (with failure details)
6. Agent can resume execution:
   - Using `ExecuteCachedTrajectory` with `start_from_step_index` from the pause point
   - Skipping failed or irrelevant steps
7. Results are verified by the agent, with corrections made as needed

### Message History

**New in v0.1:** During cached trajectory execution, a complete message history is built and returned to the agent. This includes:

- **Assistant messages**: Containing `ToolUseBlockParam` for each action
- **User messages**: Containing `ToolResultBlockParam` with:
  - Text results from tool execution
  - Screenshots (when available)
  - Error messages (on failure)

This visibility allows the agent to:
- See the current UI state via screenshots
- Understand what actions were taken
- Detect when execution has diverged from expectations
- Make informed decisions about corrections or retries

### Non-Cacheable Tools

Tools can be marked as non-cacheable by setting `is_cacheable=False` in their definition:

```python
from askui.models.shared.tools import Tool

class DebugPrintTool(Tool):
    name = "print_debug"
    description = "Print debug information about current state"
    is_cacheable = False  # This tool requires agent context

    def __call__(self, message: str) -> str:
        # Tool implementation...
        pass
```

During trajectory execution, when a non-cacheable tool is encountered:

1. `CacheExecutor` pauses execution (v0.1.1)
2. Returns `ExecutionResult` with status `NEEDS_AGENT`
3. Includes current step index and message history
4. Agent receives control to execute the step manually
5. Agent uses `ExecuteCachedTrajectory` with `start_from_step_index` to resume from next step

This mechanism is essential for tools that:
- Require runtime context (debugging, inspection)
- Make decisions based on current state
- Have side effects that shouldn't be blindly replayed
- Depend on external systems that may have changed

## Failure Handling

**New in v0.1:** Enhanced failure handling provides the agent with detailed information about what went wrong and where.

### When Execution Fails

If a step fails during trajectory execution:

1. Execution stops at the failed step
2. `ExecutionResult` includes:
   - Status: `FAILED`
   - `step_index`: Which step failed
   - `error_message`: The specific error
   - `message_history`: All actions and results up to the failure
3. Failure is recorded in cache metadata for tracking
4. Agent receives the failure information and can decide:
   - **Retry**: Execute remaining steps manually
   - **Resume**: Fix the issue and use `ExecuteCachedTrajectory` with `start_from_step_index` from next step
   - **Abort**: Report that cache needs re-recording

### Failure Tracking

Cache metadata tracks all failures:
```json
"failures": [
  {
    "timestamp": "2025-12-11T14:20:00Z",
    "step_index": 5,
    "error_message": "Element not found: login button",
    "failure_count_at_step": 2
  }
]
```

This information enables:
- Smart cache invalidation (too many failures → invalid cache)
- Debugging (which steps are problematic)
- Metrics (cache reliability over time)
- Auto-recovery strategies (skip commonly failing steps)

### Agent Recovery Options

The agent has several recovery strategies:

1. **Manual Execution**: Execute remaining steps without cache
2. **Partial Resume**: Fix the issue (e.g., wait for element) then continue from next step
3. **Skip and Continue**: Skip the failed step and continue from a later step
4. **Report Invalid**: Mark the cache as outdated and request re-recording

Example agent decision flow:
```
Trajectory fails at step 5: "Element not found: submit button"
↓
Agent takes screenshot to assess current state
↓
Agent sees submit button is present but has different text
↓
Agent clicks the button manually
↓
Agent calls ExecuteCachedTrajectory(start_from_step_index=6)
↓
Execution continues successfully
```

## Cache Parameters

**New in v0.1:** Cache Parameters enable dynamic value substitution in cached trajectories.

### Parameter Syntax

Cache Parameters use double curly braces: `{{parameter_name}}`

Valid parameter names:
- Must start with a letter or underscore
- Can contain letters, numbers, and underscores
- Examples: `{{date}}`, `{{user_name}}`, `{{order_id_123}}`

### Automatic Cache Parameter Identification

**New in v0.1!** The caching system uses AI to automatically identify and parameterize dynamic values when recording trajectories.

#### How It Works

When `parameter_identification_strategy=llm` (the default), the system:

1. **Records the trajectory** as normal during agent execution
2. **Analyzes the trajectory** using an LLM to identify dynamic values such as:
   - Dates and timestamps (e.g., "2025-12-11", "10:30 AM")
   - Usernames, emails, names (e.g., "john.doe", "test@example.com")
   - Session IDs, tokens, UUIDs, API keys
   - Dynamic text referencing current state or time
   - File paths with user-specific or time-specific components
   - Temporary or generated identifiers
3. **Generates parameter definitions** with descriptive names and documentation:
   ```json
   {
     "name": "current_date",
     "value": "2025-12-11",
     "description": "Current date in YYYY-MM-DD format"
   }
   ```
4. **Replaces values with cache_parameters** in both the trajectory AND the goal:
   - Original: `"text": "Login as john.doe"`
   - Result: `"text": "Login as {{username}}"`
5. **Saves the templated trajectory** to the cache file

#### Benefits

✅ **No manual work** - Automatically identifies dynamic values
✅ **Smart detection** - LLM understands semantic meaning (dates vs coordinates)
✅ **Descriptive** - Generates helpful descriptions for each parameter
✅ **Applies to goal** - Goal text also gets parameter replacement

#### What Gets Detected

The AI identifies values that are likely to change between executions:

**Will be detected as cache_parameters:**
- Dates: "2025-12-11", "Dec 11, 2025", "12/11/2025"
- Times: "10:30 AM", "14:45:00", "2025-12-11T10:30:00Z"
- Usernames: "john.doe", "admin_user", "test_account"
- Emails: "user@example.com", "test@domain.org"
- IDs: "uuid-1234-5678", "session_abc123", "order_9876"
- Names: "John Smith", "Jane Doe"
- Dynamic text: "Today is 2025-12-11", "Logged in as john.doe"

**Will NOT be detected as cache_parameters:**
- UI coordinates: `{"x": 100, "y": 200}`
- Fixed button labels: "Submit", "Cancel", "OK"
- Configuration values: `{"timeout": 30, "retries": 3}`
- Generic actions: "click", "type", "scroll"
- Boolean values: `true`, `false`

#### Disabling Auto-Identification

If you prefer manual parameter control:

```python
caching_settings = CachingSettings(
    strategy="record",
    writing_settings=CacheWritingSettings(
        filename="my_cache.json",
        parameter_identification_strategy="preset"  # Only detect {{...}} syntax
    )
)
```

With `parameter_identification_strategy=preset`, only manually specified cache_parameters using the `{{...}}` syntax will be detected.

#### Logging

To see what cache_parameters are being identified, enable INFO-level logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

You'll see output like:
```
INFO: Using LLM to identify cache_parameters in trajectory
INFO: Identified 3 cache_parameters in trajectory
DEBUG:   - current_date: 2025-12-11 (Current date in YYYY-MM-DD format)
DEBUG:   - username: john.doe (Username for login)
DEBUG:   - session_id: abc123 (Session identifier)
INFO: Replaced 3 parameter values in trajectory
INFO: Applied parameter replacement to goal: Login as john.doe -> Login as {{username}}
```

### Manual Cache Parameters

You can also manually create cache_parameters when recording by using the syntax in your goal description. The system will preserve `{{...}}` patterns in tool inputs.

### Providing Parameter Values

When executing a trajectory with cache_parameters, the agent must provide values:

```python
# Via ExecuteCachedTrajectory
result = execute_cached_trajectory_tool(
    trajectory_file=".cache/my_test.json",
    parameter_values={
        "current_date": "2025-12-11",
        "user_email": "test@example.com"
    }
)

# Via ExecuteCachedTrajectory with start_from_step_index
result = execute_cached_trajectory_tool(
    trajectory_file=".cache/my_test.json",
    start_from_step_index=3,  # Continue from step 3
    parameter_values={
        "current_date": "2025-12-11",
        "user_email": "test@example.com"
    }
)
```

### Parameter Validation

Before execution, the system validates that:
- All required cache_parameters have values provided
- No required cache_parameters are missing

If validation fails, execution is aborted with a clear error message listing missing cache_parameters.

### Use Cases

Cache Parameters are particularly useful for:
- **Date-dependent workflows**: Testing with current/future dates
- **User-specific actions**: Different users, emails, names
- **Order/transaction IDs**: Testing with different identifiers
- **Environment-specific values**: API endpoints, credentials
- **Parameterized testing**: Running same flow with different data

Example:
```json
{
  "name": "computer",
  "input": {
    "action": "type",
    "text": "Schedule meeting for {{meeting_date}} with {{attendee_email}}"
  }
}
```

## Limitations and Considerations

### Current Limitations

- **UI State Sensitivity**: Cached trajectories assume the UI is in the same state as when they were recorded. If the UI has changed significantly, replay may fail.
- **No on_message Callback**: When using `strategy="record"` or `strategy="both"`, you cannot provide a custom `on_message` callback, as the caching system uses this callback to record actions.
- **Verification Required**: After executing a cached trajectory, the agent should verify that the results are correct, as UI changes may cause partial failures.

### Best Practices

1. **Always Verify Results**: After cached execution, verify the outcome matches expectations
2. **Handle Failures Gracefully**: Provide clear recovery paths when trajectories fail
3. **Use Cache Parameters Wisely**: Identify dynamic values that should be parameterized
4. **Mark Non-Cacheable Tools**: Properly mark tools that require agent intervention
5. **Monitor Cache Validity**: Track execution attempts and failures to identify stale caches
6. **Test Cache Replay**: Periodically test that cached trajectories still work
7. **Version Your Caches**: Use descriptive filenames or directories for different app versions
8. **Adjust Delays**: Tune `delay_time_between_action` based on your app's responsiveness

### When to Re-Record

Consider re-recording a cached trajectory when:
- UI layout or element positions have changed significantly
- Workflow steps have been added, removed, or reordered
- Failures occur consistently at the same steps
- Execution takes significantly longer than expected
- The cache has been marked invalid due to failure patterns

## Migration from v0.0 to v0.1

**Automatic Migration:** All v0.0 cache files are automatically migrated when read by the v0.1 system. No manual intervention is required.

### What Happens During Migration

When a v0.0 cache file (simple JSON array) is read:

1. System detects v0.0 format (array instead of object with metadata)
2. Wraps trajectory in v0.1 structure
3. Adds default metadata:
   ```json
   {
     "version": "0.1",
     "created_at": "<current_time>",
     "last_executed_at": null,
     "execution_attempts": 0,
     "failures": [],
     "is_valid": true,
     "invalidation_reason": null
   }
   ```
4. Extracts any cache_parameters found in trajectory
5. Returns fully-formed `CacheFile` object

### Compatibility Guarantees

- All v0.0 cache files continue to work without modification
- Migration is performed on-the-fly during read
- Original files are not modified on disk (unless re-written)
- v0.1 system can read both formats seamlessly

### Programmatic Migration (Optional)

If you prefer to upgrade v0.0 cache files to v0.1 format on disk (rather than letting the system migrate them on-the-fly during read), you can do so programmatically:

```python
from pathlib import Path
from askui.utils.caching.cache_manager import CacheManager
import json

# Read v0.0 file (auto-migrates to v0.1 in memory)
cache_path = Path(".cache/old_cache.json")
cache_manager = CacheManager()
cached_trajectory = cache_manager.read_cache_file(cache_path)

# Write back to disk in v0.1 format
with cache_path.open("w", encoding="utf-8") as f:
    json.dump(cached_trajectory.model_dump(mode="json"), f, indent=2, default=str)
```

**Note:** Programmatic migration is optional - all v0.0 caches are automatically migrated during read operations. You only need to manually upgrade cache files if you want them in v0.1 format on disk immediately.

## Example: Complete Test Workflow with v0.1 Features

Here's a complete example showing advanced v0.1 features:

```python
import logging
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings
from askui.models.shared.tools import Tool
from askui.reporting import SimpleHtmlReporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class PrintTool(Tool):
    def __init__(self) -> None:
        super().__init__(
            name="print_tool",
            description="""
                Print something to the console
            """,
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": """
                    The text that should be printed to the console
                    """,
                    },
                },
                "required": ["text"],
            },
        )
        self.is_cacheable = False

    # Agent will detect cache_parameters and provide new values:
    def __call__(self, text: str) -> None:
        print(text)

# Step 2: Replay with different values
print("\nReplaying registration with new user...")
with VisionAgent() as agent:
    agent.act(
        goal="""Log in to the application.

        If the cache file "user_login.json" is available, please use it to replay
        the login sequence. It contains the steps to navigate to the login page and
        authenticate with the test credentials.""",
        caching_settings=CachingSettings(
            strategy="read",
            cache_dir="test_cache",
            execute_cached_trajectory_tool_settings=CachedExecutionToolSettings(
                delay_time_between_action=0.75
            )
        )
    )


if __name__ == "__main__":
    goal = """Please open a new window in google chrome by right clicking on the icon in the Dock at the bottom of the screen.
            Then, navigate to www.askui.com and print a brief summary all the screens that you have seen during the execution.
            Describe them one by one, e.g. 1. Screen: Lorem Ipsum, 2. Screen: ....
            One sentence per screen is sufficient.
            Do not scroll on the screens for that!
            Just summarize the content that is or was visible on the screen.
            If available, you can use cache file at caching_demo.json
            """
    caching_settings = CachingSettings(
        strategy="both", cache_dir=".askui_cache", filename="caching_demo.json"
    )
    # first act will create the cache file
    with VisionAgent(
        display=1, reporters=[SimpleHtmlReporter()], act_tools=[PrintTool()]
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)

    # second act will read and execute the cached file
    goal = goal.replace("www.askui.com", "www.caesr.ai")
    with VisionAgent(
        display=1, reporters=[SimpleHtmlReporter()], act_tools=[PrintTool()]
    ) as agent:
        agent.act(goal, caching_settings=caching_settings)
```

## Future Enhancements

Planned features for future versions:

- **Visual Validation**: Screenshot comparison using perceptual hashing (aHash) to detect UI changes
- **Cache Invalidation Strategies**: Configurable validators for automatic cache invalidation
- **Cache Management Tools**: Tools for listing, validating, and invalidating caches
- **Smart Retry**: Automatic retry with adjustments when specific failure patterns are detected
- **Cache Analytics**: Metrics dashboard showing cache performance and reliability
- **Differential Caching**: Record only changed steps when updating existing caches

## Troubleshooting

### Common Issues

**Issue**: Cached trajectory fails to execute
- **Cause**: UI has changed since recording
- **Solution**: Take a screenshot to compare, re-record the trajectory, or manually execute failing steps

**Issue**: "Missing required cache_parameters" error
- **Cause**: Trajectory contains cache_parameters but values weren't provided
- **Solution**: Check cache metadata for required cache_parameters and provide values via `parameter_values` parameter

**Issue**: Execution pauses unexpectedly
- **Cause**: Trajectory contains non-cacheable tool
- **Solution**: Execute the non-cacheable step manually, then use `ExecuteCachedTrajectory` with `start_from_step_index` to resume

**Issue**: Actions execute too quickly, causing failures
- **Cause**: `delay_time_between_action` is too short for your application
- **Solution**: Increase delay in `CachedExecutionToolSettings` (e.g., from 0.5 to 1.0 seconds)

**Issue**: "Tool not found in toolbox" error
- **Cause**: Cached trajectory uses a tool that's no longer available
- **Solution**: Re-record the trajectory with current tools, or add the missing tool back

### Debug Tips

1. **Check message history**: After execution, review `message_history` in the result to see exactly what happened
2. **Monitor failure metadata**: Track `execution_attempts` and `failures` in cache metadata
3. **Test incrementally**: Use `ExecuteCachedTrajectory` with `start_from_step_index` to test specific sections of a trajectory
4. **Verify cache_parameters**: Print cache metadata to see what cache_parameters are expected
5. **Adjust delays**: If timing issues occur, increase `delay_time_between_action` incrementally

For more help, see the [GitHub Issues](https://github.com/askui/askui-python-sdk/issues) or contact support.
