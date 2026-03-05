# Caching (Experimental)

The caching mechanism allows you to record and replay agent action sequences (trajectories) for faster and more robust test execution. This feature is particularly useful for regression testing, where you want to replay known-good interaction sequences to verify that your application still behaves correctly.

## Overview

The caching system works by recording all tool use actions (mouse movements, clicks, typing, etc.) performed by the agent during an `act()` execution. These recorded sequences can then be replayed in subsequent executions, allowing the agent to skip the decision-making process and execute the actions directly.

## Caching Strategies

The caching mechanism supports three strategies, configured via the `caching_settings` parameter in the `act()` method:

- **`None`** (default): No caching is used. The agent executes normally without recording or replaying actions.
- **`"record"`**: Records all agent actions to a cache file for future replay.
- **`"execute"`**: Provides tools to the agent to list and execute previously cached trajectories.
- **`"auto"`**: Combines execute and record modes - the agent can use existing cached trajectories and will also record new ones.

## Configuration

Caching is configured using the `CachingSettings` class:

```python
from askui.models.shared.settings import (
    CachingSettings,
    CacheExecutionSettings,
    CacheWritingSettings,
)

caching_settings = CachingSettings(
    strategy="record",       # One of: "execute", "record", "auto", or None
    cache_dir=".askui_cache", # Directory to store cache files
    writing_settings=CacheWritingSettings(
        filename="my_test.json"  # Filename for the cache file (optional)
    ),
    execution_settings=CacheExecutionSettings(
        delay_time_between_actions=1.0  # Delay in seconds between each cached action
    ),
)
```

### Parameters

- **`strategy`**: The caching strategy to use (`"execute"`, `"record"`, `"auto"`, or `None`).
- **`cache_dir`**: Directory where cache files are stored. Defaults to `".askui_cache"`.
- **`writing_settings`**: Configuration for cache recording (optional). See [Writing Settings](#writing-settings) below.
- **`execution_settings`**: Configuration for cache playback (optional). See [Execution Settings](#execution-settings) below.

### Writing Settings

The `CacheWritingSettings` class allows you to configure how cache files are recorded:

```python
from askui.models.shared.settings import CacheWritingSettings

writing_settings = CacheWritingSettings(
    filename="my_test.json"  # Name for the cache file (auto-generated if empty)
)
```

#### Parameters

- **`filename`**: Name of the cache file to write. If not specified, a timestamped filename will be generated automatically (format: `cached_trajectory_YYYYMMDDHHMMSSffffff.json`).

### Execution Settings

The `CacheExecutionSettings` class allows you to configure how cached trajectories are executed:

```python
from askui.models.shared.settings import CacheExecutionSettings

execution_settings = CacheExecutionSettings(
    delay_time_between_actions=1.0  # Delay in seconds between each action (default: 1.0)
)
```

#### Parameters

- **`delay_time_between_actions`**: The time to wait (in seconds) between executing consecutive cached actions. This delay helps ensure UI elements can materialize before the next action is executed. Defaults to `1.0` seconds.

You can adjust this value based on your application's responsiveness:
- For faster applications or quick interactions, you might use a smaller delay (e.g., `0.2` or `0.5` seconds)
- For slower applications or complex UI updates, you might need a longer delay (e.g., `2.0` or `3.0` seconds)

## Usage Examples

### Recording a Cache

Record agent actions to a cache file for later replay:

```python
from askui import ComputerAgent
from askui.models.shared.settings import CachingSettings, CacheWritingSettings

with ComputerAgent() as agent:
    agent.act(
        goal="Fill out the login form with username 'admin' and password 'secret123'",
        caching_settings=CachingSettings(
            strategy="record", # you could also use "auto" here
            writing_settings=CacheWritingSettings(
                filename="login_test.json"
            ),
        )
    )
```

After execution, a cache file will be created at `.askui_cache/login_test.json` containing all the tool use actions performed by the agent.

### Executing from Cache (Replaying)

Provide the agent with access to previously recorded trajectories:

```python
from askui import ComputerAgent
from askui.models.shared.settings import CachingSettings

with ComputerAgent() as agent:
    agent.act(
        goal="Fill out the login form",
        caching_settings=CachingSettings(
            strategy="execute", # you could also use "auto" here
        )
    )
```

When using `strategy="execute"`, the agent receives two additional tools:

1. **`retrieve_available_trajectories_tool`**: Lists all available cache files in the cache directory
2. **`execute_cached_executions_tool`**: Executes a specific cached trajectory

The agent will automatically check if a relevant cached trajectory exists and use it if appropriate. After executing a cached trajectory, the agent will verify the results and make corrections if needed.

### Referencing Cache Files in Goal Prompts

When using `strategy="execute"` or `strategy="auto"`, **you need to inform the agent about which cache files are available and when to use them**. This is done by including cache file information directly in your goal prompt.

#### Explicit Cache File References

For specific tasks, mention the cache file name and what it accomplishes:

```python
from askui import ComputerAgent
from askui.models.shared.settings import CachingSettings

with ComputerAgent() as agent:
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
from askui import ComputerAgent
from askui.models.shared.settings import CachingSettings

test_id = "TEST_001"

with ComputerAgent() as agent:
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
from askui import ComputerAgent
from askui.models.shared.settings import CachingSettings

with ComputerAgent() as agent:
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
from askui import ComputerAgent
from askui.models.shared.settings import CachingSettings

with ComputerAgent() as agent:
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
from askui import ComputerAgent
from askui.models.shared.settings import CachingSettings, CacheExecutionSettings

with ComputerAgent() as agent:
    agent.act(
        goal="Fill out the login form",
        caching_settings=CachingSettings(
            strategy="execute",
            execution_settings=CacheExecutionSettings(
                delay_time_between_actions=2.0  # Wait 2 seconds between each action
            ),
        )
    )
```

This is particularly useful when:
- Your application has animations or transitions that need time to complete
- UI elements take time to become interactive after appearing
- You're testing on slower hardware or environments

### Using Auto Strategy

Enable both reading and writing simultaneously:

```python
from askui import ComputerAgent
from askui.models.shared.settings import CachingSettings, CacheWritingSettings

with ComputerAgent() as agent:
    agent.act(
        goal="Complete the checkout process",
        caching_settings=CachingSettings(
            strategy="auto",
            writing_settings=CacheWritingSettings(
                filename="checkout_test.json"
            ),
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

In write mode, the `CacheManager`:

1. Extracts tool use blocks from the full message history when the conversation ends
2. Writes them to a JSON file
3. Automatically skips writing if a cached execution was used (to avoid recording replays)

### Read Mode

In read mode:

1. Two caching tools are added to the agent's toolbox
2. A special system prompt (`CACHE_USE_PROMPT`) is appended to instruct the agent on how to use trajectories
3. The agent can call `retrieve_available_trajectories_tool` to see available cache files
4. The agent can call `execute_cached_executions_tool` with a trajectory file path to replay it
5. During replay, each tool use block is executed sequentially with a configurable delay between actions (default: 1.0 seconds)
6. Screenshot and trajectory retrieval tools are skipped during replay
7. The agent is instructed to verify results after replay and make corrections if needed

The delay between actions can be customized using `CacheExecutionSettings` to accommodate different application response times.

## Limitations

- **UI State Sensitivity**: Cached trajectories assume the UI is in the same state as when they were recorded. If the UI has changed, the replay may fail or produce incorrect results.
- **Verification Required**: After executing a cached trajectory, the agent should verify that the results are correct, as UI changes may cause partial failures.

## Example: Complete Test Workflow

Here's a complete example showing how to record and replay a test:

```python
from askui import ComputerAgent
from askui.models.shared.settings import (
    CachingSettings,
    CacheExecutionSettings,
    CacheWritingSettings,
)

# Step 1: Record a successful login flow
print("Recording login flow...")
with ComputerAgent() as agent:
    agent.act(
        goal="Navigate to the login page and log in with username 'testuser' and password 'testpass123'",
        caching_settings=CachingSettings(
            strategy="record",
            cache_dir="test_cache",
            writing_settings=CacheWritingSettings(
                filename="user_login.json"
            ),
        )
    )

# Step 2: Later, replay the login flow for regression testing
print("\nReplaying login flow for regression test...")
with ComputerAgent() as agent:
    agent.act(
        goal="""Log in to the application.

        If the cache file "user_login.json" is available, please use it to replay
        the login sequence. It contains the steps to navigate to the login page and
        authenticate with the test credentials.""",
        caching_settings=CachingSettings(
            strategy="execute",
            cache_dir="test_cache",
            execution_settings=CacheExecutionSettings(
                delay_time_between_actions=2.0
            ),
        )
    )
```
