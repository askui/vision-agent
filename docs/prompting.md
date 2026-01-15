# System Prompts

System prompts define how the Vision Agent behaves when executing tasks through the `act()` command. A well-structured system prompt provides the agent with the necessary context, capabilities, and constraints to successfully interact with your application's UI across different devices and platforms.

## Overview

The Vision Agent uses system prompts to understand:
- What actions it can perform
- What device/platform it's operating on
- Specific information about your UI
- How to format execution reports
- Special rules or edge cases to handle

The default prompts work well for general use cases, but customizing them for your specific application can significantly improve reliability and performance.

## Prompt Structure

System prompts should consist of six distinct parts, each wrapped in XML tags:

| Part | Required | Purpose |
|------|----------|---------|
| System Capabilities | Yes | Defines what the agent can do and how it should behave |
| Device Information | Yes | Provides platform-specific context (desktop, mobile, web) |
| UI Information | No (but strongly recommended!) | Custom information about your specific UI |
| Report Format | Yes | Specifies how to format execution results |
| Cache Use | No | Specifices when and how the agent should use cache files |
| Additional Rules | No | Special handling for edge cases or known issues |

### 1. System Capabilities

Defines the agent's core capabilities and operational guidelines.

**Default prompts available:**
- `COMPUTER_USE_CAPABILITIES` - For desktop applications
- `WEB_BROWSER_CAPABILITIES` - For web applications
- `ANDROID_CAPABILITIES` - For Android devices

**Important:** We recommend using the default AskUI capabilities unless you have specific requirements, as custom capabilities can lead to unexpected behavior.

### 2. Device Information

Provides platform-specific context to help the agent understand the environment.

**Default options:**
- `DESKTOP_DEVICE_INFORMATION` - Platform, architecture, internet access
- `WEB_AGENT_DEVICE_INFORMATION` - Browser environment details
- `ANDROID_DEVICE_INFORMATION` - ADB connection, device type

### 3. UI Information

**This is the most important part to customize for your application.**

Provide specific details about your UI that the agent needs to know:

- Location of key functions and features
- Non-standard interaction patterns
- Common navigation paths
- Areas where users typically encounter issues
- Actions that should NOT be performed

### 4. Report Format

Specifies how the agent should format its execution report.

**Default options:**
- `MD_REPORT_FORMAT` - Markdown formatted summary with observations
- `NO_REPORT_FORMAT` - No formal report required

### 5. Cache Use Prompt

Will be added automatically depending on your caching settings.

### 6. Additional Rules

Optional rules for handling specific edge cases or known issues with your application.

**Use cases:**
- Browser-specific workarounds (e.g., Firefox startup wizards)
- Special handling for specific UI states
- Recovery strategies for common failure scenarios

## Creating Custom Prompts

### Using Factory Functions (Recommended)

The simplest way to create custom prompts:

```python
from askui.prompts.act_prompts import create_web_agent_prompt

# Create prompt with custom UI information
prompt = create_web_agent_prompt(
    ui_information="""
    **Navigation:**
    - Main menu is accessible via hamburger icon in top-left corner
    - Search functionality is in the header on all pages

    **Login Flow:**
    - Username field must be filled before password field becomes active
    - "Remember me" checkbox should NOT be used in automated tests

    **Common Issues:**
    - Loading spinner may appear for 2-3 seconds after clicking "Submit"
    - Error messages appear as toast notifications in top-right corner
    """,
    additional_rules="""
    - Always wait for the loading spinner to disappear before proceeding
    - Never click "Save and Exit" without explicit user confirmation
    """
)

# Use in agent
from askui import WebVisionAgent
from askui.models.shared.settings import ActSettings, MessageSettings

with WebVisionAgent() as agent:
    agent.act(
        "Log in with username 'testuser' and password 'testpass123'",
        # CAUTION: this will also override all other MessageSettings
        # eventually provided earlier!
        settings=ActSettings(messages=MessageSettings(system=prompt))
    )
```

Available factory functions:
- `create_computer_agent_prompt()` - Desktop applications
- `create_web_agent_prompt()` - Web applications
- `create_android_agent_prompt()` - Android devices

### Using ActSystemPrompt Directly

For full control over all prompt components:

```python
from askui.models.shared.prompts import ActSystemPrompt
from askui.prompts.act_prompts import (
    WEB_BROWSER_CAPABILITIES,
    WEB_AGENT_DEVICE_INFORMATION,
    NO_REPORT_FORMAT,
)

prompt = ActSystemPrompt(
    system_capabilities=WEB_BROWSER_CAPABILITIES,
    device_information=WEB_AGENT_DEVICE_INFORMATION,
    ui_information="Your custom UI information here",
    report_format=NO_REPORT_FORMAT,
    additional_rules="Your additional rules here"
)
```

### Power User Override (Not Recommended)

**Warning:** This feature is intended for power users only and can lead to unexpected behavior.

`ActSystemPrompt` includes a `prompt` field that completely overrides all structured prompt parts when set. This is useful only if you need full control over the exact prompt text:

```python
from askui.models.shared.prompts import ActSystemPrompt
from askui.models.shared.settings import ActSettings, MessageSettings

# Power user override - ignores all other prompt fields
prompt = ActSystemPrompt(
    prompt="Your completely custom system prompt here",
    # All other fields will be ignored when prompt is set:
    system_capabilities="Ignored",
    device_information="Ignored",
    # ... etc
)

with WebVisionAgent() as agent:
    agent.act(
        "Your task",
        settings=ActSettings(messages=MessageSettings(system=prompt))
    )
```

**Important limitations:**
- ⚠️ Using the `prompt` field will trigger a `UserWarning` on model creation
- ⚠️ All structured prompt parts (capabilities, device info, etc.) are completely ignored
- ✅ Other `MessageSettings` fields remain unchanged (betas, thinking, max_tokens, temperature, tool_choice)
- ✅ Only the system prompt text itself is affected - all other settings remain at their configured values

**When to use this:**
- You have extensive experience with prompt engineering
- You need to experiment with completely different prompt structures
- You're conducting research or debugging specific prompt behaviors

**When NOT to use this:**
- For normal customization needs (use factory functions or structured fields instead)
- When you want to maintain the tested structure of default prompts
- In production environments where reliability is critical

### Modifying Default Prompts

You can extend the default prompts with your own content:

```python
from askui.prompts.act_prompts import (
    create_computer_agent_prompt,
    BROWSER_SPECIFIC_RULES,
)

# Add your own rules to the defaults
custom_rules = f"""
{BROWSER_SPECIFIC_RULES}

**Application-Specific Rules:**
- Always verify the page title before proceeding with actions
- Wait 1 second after navigation before taking screenshots
- Ignore popup notifications that appear during test execution
"""

prompt = create_computer_agent_prompt(
    ui_information="E-commerce checkout flow with 3-step process",
    additional_rules=custom_rules
)
```

## Best Practices

### Language and Clarity

- **Use consistent English**: Stick to clear English throughout your prompt. Mixed languages or non-English prompts will degrade performance.
- **Be specific and detailed**: Provide as much relevant detail as possible. Over-specification is better than under-specification.
- **Use structured format**: Organize information with bullet points and clear sections.
- **Avoid contradictions**: Ensure rules don't conflict with each other.

### UI Information

- **Document navigation patterns**: Explain how users navigate through your application.
- **Identify unique elements**: Point out non-standard UI components or interactions.
- **Specify timing requirements**: Note any delays, loading states, or async operations.
- **List forbidden actions**: Explicitly state what the agent should NOT do.

### Additional Rules

- **Target specific issues**: Use this section to address known failure scenarios.
- **Provide context**: Explain when and why a rule applies.
- **Include examples**: Show concrete examples of the situation you're addressing.
- **Keep it current**: Update rules as your application changes.

### Testing and Iteration

1. **Start with defaults**: Use default prompts initially to establish a baseline.
2. **Add UI information**: Customize with your application-specific details.
3. **Monitor failures**: Track where the agent struggles or fails.
4. **Refine rules**: Add additional rules to handle discovered edge cases.
5. **Test changes**: Verify that prompt changes improve reliability.

## Available Constants

Import these constants from `askui.prompts.act_prompts`:

**System Capabilities:**
- `GENERAL_CAPABILITIES`
- `COMPUTER_USE_CAPABILITIES`
- `ANDROID_CAPABILITIES`
- `WEB_BROWSER_CAPABILITIES`

**Device Information:**
- `DESKTOP_DEVICE_INFORMATION`
- `ANDROID_DEVICE_INFORMATION`
- `WEB_AGENT_DEVICE_INFORMATION`

**Report Formats:**
- `MD_REPORT_FORMAT`
- `NO_REPORT_FORMAT`

**Additional Rules:**
- `BROWSER_SPECIFIC_RULES`
- `BROWSER_INSTALL_RULES`
- `ANDROID_RECOVERY_RULES`

## Example: Complete Custom Prompt

```python
from askui import WebVisionAgent
from askui.prompts.act_prompts import create_web_agent_prompt
from askui.models.shared.settings import ActSettings, MessageSettings

# Create comprehensive custom prompt
prompt = create_web_agent_prompt(
    ui_information="""
    **Application Overview:**
    - Multi-page e-commerce application with product catalog and checkout
    - Uses single-page navigation with URL updates

    **Key Features:**
    - Product search in header (always visible)
    - Shopping cart icon shows item count
    - Checkout is 3-step process: Cart → Shipping → Payment

    **Important Elements:**
    - "Add to Cart" buttons are blue with white text
    - Price displays always show currency symbol ($)
    - Out-of-stock items show "Notify Me" instead of "Add to Cart"

    **Navigation:**
    - Home: Click logo in top-left
    - Categories: Dropdown menu under "Shop" in header
    - Cart: Click cart icon in top-right
    - Account: Click user icon in top-right

    **Common Patterns:**
    - All forms require clicking "Next" or "Continue" to proceed
    - Error messages appear in red above form fields
    - Success messages appear as green banner at top of page

    **Timing Considerations:**
    - Product images may take 1-2 seconds to load
    - Cart updates trigger 500ms animation
    - Checkout validation shows spinner for 1-3 seconds

    **DO NOT:**
    - Click "Complete Purchase" without explicit user confirmation
    - Submit payment information
    - Delete items from saved lists
    """,
    additional_rules="""
    - Always verify cart contents before proceeding to checkout
    - Wait for page transitions to complete before taking next action
    - If "Out of Stock" message appears, report it and stop execution
    - Ignore promotional popups that may appear during browsing
    """
)

# Use the prompt
with WebVisionAgent() as agent:
    agent.act(
        "Find a laptop under $1000 and add it to cart",
        # CAUTION: this will also override all other MessageSettings
        # eventually provided earlier!
        settings=ActSettings(messages=MessageSettings(system=prompt))
    )
```
