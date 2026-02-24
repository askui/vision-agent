# Using Agents

AskUI Vision Agent provides three predefined agent types for different automation targets. All agents share the same core API (`act()`, `get()`, `locate()`) but are optimized for their respective platforms. Each agent comes with its own system prompt tailored to its platform-specific tools and capabilities.

## ComputerAgent

Use this agent for desktop automation on Windows, macOS, and Linux. Uses AskUI Agent OS to control mouse, keyboard, and capture screenshots.

```python
from askui import ComputerAgent

with ComputerAgent() as agent:
    agent.act("Open the mail app and summarize all unread emails")
```

**Default tools:** `screenshot`, `mouse_click`, `mouse_move`, `mouse_scroll`, `mouse_hold_down`, `mouse_release`, `type`, `keyboard_tap`, `keyboard_pressed`, `keyboard_release`, `get_mouse_position`, `get_system_info`, `list_displays`, `retrieve_active_display`, `set_active_display`

## AndroidAgent

Use this agent for automation of Android devices via ADB. Supports tapping, swiping, typing, and shell commands.

```python
from askui import AndroidAgent

with AndroidAgent(device=0) as agent:
    agent.tap("Login button")
    agent.swipe(start=(500, 1000), end=(500, 300))
    agent.act("Navigate to settings and enable notifications")
```

Requires the `android` dependency installed (`pip install askui[android]`) and a connected device (physical or emulator).

**Default tools:** `screenshot`, `tap`, `type`, `swipe`, `drag_and_drop`, `key_tap_event`, `key_combination`, `shell`, `select_device_by_serial_number`, `select_display_by_unique_id`, `get_connected_devices_serial_numbers`, `get_connected_displays_infos`, `get_current_connected_device_infos`

## WebVisionAgent

For web browser automation using Playwright. Extends `ComputerAgent` with web-specific tools like navigation, URL handling, and page title retrieval.

```python
from askui import WebVisionAgent

with WebVisionAgent() as agent:
    agent.tools.os.goto("https://example.com")
    agent.click("Sign In")
    agent.act("Fill out the contact form and submit")
```

**Default tools:** All `ComputerAgent` tools plus `goto`, `back`, `forward`, `get_page_title`, `get_page_url`

## Choosing an Agent

| Target | Agent | Backend |
|--------|-------|---------|
| Desktop (Windows/macOS/Linux) | `ComputerAgent` | AskUI Agent OS (gRPC) |
| Android devices | `AndroidAgent` | ADB |
| Web browsers | `WebVisionAgent` | Playwright |
