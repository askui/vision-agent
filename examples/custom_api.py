"""Examples demonstrating how to use custom MessagesApi configurations.

This script shows three different ways to configure the MessagesApi for your agent:
1. Using the default AskUI MessagesApi (no configuration needed)
2. Providing a custom MessagesApi to VisionAgent on initialization
3. Providing a custom MessagesApi to a speaker and passing it to act()

Priority hierarchy:
- Speaker init (highest priority)
- act() method parameter
- VisionAgent init parameter (lowest priority)
"""

from askui import VisionAgent
from askui.locators.serializers import VlmLocatorSerializer
from askui.models.anthropic.factory import create_api_client
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.speaker import AskUIAgent, Speakers


def example_1_default_api():
    """Example 1: Using the default AskUI MessagesApi.

    This is the simplest approach - no MessagesApi configuration needed.
    The agent will automatically use the AskUI API endpoint.
    """
    print("\n=== Example 1: Default AskUI MessagesApi ===")

    with VisionAgent() as agent:
        # No MessagesApi configuration needed
        # Uses default AskUI endpoint automatically
        agent.act("Open the calculator application")
        print("✓ Used default AskUI MessagesApi")


def example_2_api_on_vision_agent_init():
    """Example 2: Providing MessagesApi to VisionAgent on initialization.

    This approach sets a default MessagesApi for all act() calls in this agent.
    Useful when you want all operations to use a specific API endpoint.
    """
    print("\n=== Example 2: MessagesApi on VisionAgent init ===")

    # Create a custom MessagesApi pointing to Anthropic's API
    custom_messages_api = AnthropicMessagesApi(
        client=create_api_client(api_provider="anthropic"),
        locator_serializer=VlmLocatorSerializer(),
    )

    with VisionAgent(act_api=custom_messages_api) as agent:
        # This act() call will use the Anthropic API
        agent.act("Open the calculator application")
        print("✓ Used Anthropic MessagesApi from VisionAgent init")

        # You can still override per act() call if needed
        askui_api = AnthropicMessagesApi(
            client=create_api_client(api_provider="askui"),
            locator_serializer=VlmLocatorSerializer(),
        )
        agent.act(
            "Calculate 2 + 2",
            messages_api=askui_api,  # Override with AskUI API for this call
        )
        print("✓ Overrode with AskUI MessagesApi in act() call")


def example_3_api_via_speaker():
    """Example 3: Providing MessagesApi to a speaker.

    This approach gives you the most control - you can configure different
    speakers with different API endpoints and choose which one to use per act() call.
    This is the highest priority configuration.
    """
    print("\n=== Example 3: MessagesApi via custom speaker ===")

    # Create a speaker with Anthropic API
    anthropic_api = AnthropicMessagesApi(
        client=create_api_client(api_provider="anthropic"),
        locator_serializer=VlmLocatorSerializer(),
    )
    anthropic_speaker = AskUIAgent(
        messages_api=anthropic_api,
        model_name="claude-sonnet-4-20250514",  # Can also set model per speaker
    )

    # Create a speaker with AskUI API
    askui_api = AnthropicMessagesApi(
        client=create_api_client(api_provider="askui"),
        locator_serializer=VlmLocatorSerializer(),
    )
    askui_speaker = AskUIAgent(
        messages_api=askui_api, model_name="claude-sonnet-4-20250514"
    )

    with VisionAgent() as agent:
        # Use Anthropic API for this call
        agent.act(
            "Open the calculator application",
            speakers=Speakers({"AskUIAgent": anthropic_speaker}),
        )
        print("✓ Used Anthropic MessagesApi from custom speaker")

        # Use AskUI API for this call
        agent.act("Calculate 2 + 2", speakers=Speakers({"AskUIAgent": askui_speaker}))
        print("✓ Used AskUI MessagesApi from different custom speaker")


def example_4_priority_demonstration():
    """Example 4: Demonstrating the priority hierarchy.

    Shows how the priority chain works:
    Speaker init > act() parameter > VisionAgent init
    """
    print("\n=== Example 4: Priority hierarchy demonstration ===")

    # Setup three different MessagesApi instances
    agent_level_api = AnthropicMessagesApi(
        client=create_api_client(api_provider="askui"),
        locator_serializer=VlmLocatorSerializer(),
    )

    act_level_api = AnthropicMessagesApi(
        client=create_api_client(api_provider="anthropic"),
        locator_serializer=VlmLocatorSerializer(),
    )

    speaker_level_api = AnthropicMessagesApi(
        client=create_api_client(api_provider="anthropic"),
        locator_serializer=VlmLocatorSerializer(),
    )

    # Create VisionAgent with agent-level API (lowest priority)
    with VisionAgent(act_api=agent_level_api) as agent:
        print("VisionAgent configured with AskUI API (lowest priority)")

        # Test 1: Only agent-level API set
        agent.act("Open calculator")
        print("  ✓ Priority 1: Used AskUI API from VisionAgent init")

        # Test 2: Override with act-level API (medium priority)
        agent.act("Calculate 2 + 2", messages_api=act_level_api)
        print("  ✓ Priority 2: Used Anthropic API from act() parameter")

        # Test 3: Override with speaker-level API (highest priority)
        custom_speaker = AskUIAgent(messages_api=speaker_level_api)
        agent.act(
            "Show result",
            messages_api=act_level_api,  # This will be ignored!
            speakers=Speakers({"AskUIAgent": custom_speaker}),
        )
        print("  ✓ Priority 3: Used Anthropic API from speaker init (highest)")


def example_5_model_name_configuration():
    """Example 5: Configuring model names with the same priority hierarchy.

    Just like MessagesApi, model_name follows the same priority chain:
    Speaker init > act() parameter > VisionAgent init
    """
    print("\n=== Example 5: Model name configuration ===")

    # Create VisionAgent with default model name
    with VisionAgent(model_name="claude-sonnet-4-20250514") as agent:
        print("VisionAgent configured with claude-sonnet-4-20250514")

        # Use default model from VisionAgent init
        agent.act("Open calculator")
        print("  ✓ Used model from VisionAgent init")

        # Override with model in act() call
        agent.act("Calculate 2 + 2", model_name="claude-opus-4-20241029")
        print("  ✓ Overrode with claude-opus-4-20241029 in act() call")

        # Override with model in speaker (highest priority)
        custom_speaker = AskUIAgent(model_name="claude-haiku-4-20250514")
        agent.act(
            "Show result",
            model_name="claude-opus-4-20241029",  # This will be ignored!
            speakers=Speakers({"AskUIAgent": custom_speaker}),
        )
        print("  ✓ Used claude-haiku-4-20250514 from speaker (highest priority)")


def main():
    """Run all examples."""
    example_1_default_api()
    example_2_api_on_vision_agent_init()
    example_3_api_via_speaker()
    example_4_priority_demonstration()
    example_5_model_name_configuration()


if __name__ == "__main__":
    main()
