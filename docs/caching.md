# Caching

The caching mechanism allows you to record and replay agent action sequences (trajectories) for faster and more robust test execution. This feature is particularly useful for regression testing, where you want to replay known-good interaction sequences to verify that your application still behaves correctly.

## Overview

The caching system works by recording all tool use actions (mouse movements, clicks, typing, etc.) performed by the agent during an `act()` execution. These recorded sequences can then be replayed in subsequent executions, allowing the agent to skip the decision-making process and execute the actions directly.

## Caching Strategies

The caching mechanism supports four strategies, configured via the `caching_settings` parameter in the `act()` method:

- **`"no"`** (default): No caching is used. The agent executes normally without recording or replaying actions.
- **`"write"`**: Records all agent actions to a cache file for future replay.
- **`"read"`**: Provides tools to the agent to list and execute previously cached trajectories.
- **`"both"`**: Combines read and write modes - the agent can use existing cached trajectories and will also record new ones.

## Configuration

Caching is configured using the `CachingSettings` class:

```python
from askui.models.shared.settings import CachingSettings

caching_settings = CachingSettings(
    strategy="write",        # One of: "read", "write", "both", "no"
    cache_dir=".cache",      # Directory to store cache files
    filename="my_test.json"  # Filename for the cache file (optional for write mode)
)
```

### Parameters

- **`strategy`**: The caching strategy to use (`"read"`, `"write"`, `"both"`, or `"no"`).
- **`cache_dir`**: Directory where cache files are stored. Defaults to `".cache"`.
- **`filename`**: Name of the cache file to write to or read from. If not specified in write mode, a timestamped filename will be generated automatically (format: `cached_trajectory_YYYYMMDDHHMMSSffffff.json`).

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
            strategy="write",
            cache_dir=".cache",
            filename="login_test.json"
        )
    )
```

After execution, a cache file will be created at `.cache/login_test.json` containing all the tool use actions performed by the agent.

### Reading from Cache (Replaying)

Provide the agent with access to previously recorded trajectories:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

with VisionAgent() as agent:
    agent.act(
        goal="Fill out the login form",
        caching_settings=CachingSettings(
            strategy="read",
            cache_dir=".cache"
        )
    )
```

When using `strategy="read"`, the agent receives two additional tools:

1. **`retrieve_available_trajectories_tool`**: Lists all available cache files in the cache directory
2. **`execute_cached_executions_tool`**: Executes a specific cached trajectory

The agent will automatically check if a relevant cached trajectory exists and use it if appropriate. After executing a cached trajectory, the agent will verify the results and make corrections if needed.

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
            filename="checkout_test.json"
        )
    )
```

In this mode:
- The agent can use existing cached trajectories to speed up execution
- New actions will be recorded to the specified cache file
- If a cached execution is used, no new cache file will be written (to avoid duplicates)

## Cache File Format

Cache files are JSON files containing an array of tool use blocks. Each block represents a single tool invocation with the following structure:

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
    },
    {
        "type": "tool_use",
        "id": "toolu_02AbCdEfGhIjKlMnOpQrStUv",
        "name": "computer",
        "input": {
            "action": "left_click"
        }
    },
    {
        "type": "tool_use",
        "id": "toolu_03AbCdEfGhIjKlMnOpQrStUv",
        "name": "computer",
        "input": {
            "action": "type",
            "text": "admin"
        }
    }
]
```

Note: Screenshot actions are excluded from cached trajectories as they don't modify the UI state.

## How It Works

### Write Mode

In write mode, the `CacheWriter` class:

1. Intercepts all assistant messages via a callback function
2. Extracts tool use blocks from the messages
3. Stores them in memory during execution
4. Writes them to a JSON file when the agent finishes (on `stop_reason="end_turn"`)
5. Automatically skips writing if a cached execution was used (to avoid recording replays)

### Read Mode

In read mode:

1. Two caching tools are added to the agent's toolbox
2. A special system prompt (`CACHE_USE_PROMPT`) is appended to instruct the agent on how to use trajectories
3. The agent can call `retrieve_available_trajectories_tool` to see available cache files
4. The agent can call `execute_cached_executions_tool` with a trajectory file path to replay it
5. During replay, each tool use block is executed sequentially with a 2-second delay between actions
6. Screenshot and trajectory retrieval tools are skipped during replay
7. The agent is instructed to verify results after replay and make corrections if needed

## Limitations

- **UI State Sensitivity**: Cached trajectories assume the UI is in the same state as when they were recorded. If the UI has changed, the replay may fail or produce incorrect results.
- **No on_message Callback**: When using `strategy="write"` or `strategy="both"`, you cannot provide a custom `on_message` callback, as the caching system uses this callback to record actions.
- **Verification Required**: After executing a cached trajectory, the agent should verify that the results are correct, as UI changes may cause partial failures.

## Example: Complete Test Workflow

Here's a complete example showing how to record and replay a test:

```python
from askui import VisionAgent
from askui.models.shared.settings import CachingSettings

# Step 1: Record a successful login flow
print("Recording login flow...")
with VisionAgent() as agent:
    agent.act(
        goal="Navigate to the login page and log in with username 'testuser' and password 'testpass123'",
        caching_settings=CachingSettings(
            strategy="write",
            cache_dir="test_cache",
            filename="user_login.json"
        )
    )

# Step 2: Later, replay the login flow for regression testing
print("\nReplaying login flow for regression test...")
with VisionAgent() as agent:
    agent.act(
        goal="Log in to the application",
        caching_settings=CachingSettings(
            strategy="read",
            cache_dir="test_cache"
        )
    )
```
