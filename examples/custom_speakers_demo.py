"""
Example demonstrating custom speakers with VisionAgent.

This example shows how to create custom speakers that can be passed to the
VisionAgent's act() command. Speakers handle different conversation steps and
can implement custom logic for specific scenarios.

Custom speakers can be useful for:
- Implementing human-in-the-loop workflows
- Adding custom validation or approval steps
- Integrating external systems or APIs
- Creating specialized conversation flows
"""

import logging

from askui import VisionAgent
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.prompts import ActSystemPrompt
from askui.models.shared.settings import ActSettings, MessageSettings
from askui.models.shared.tools import Tool
from askui.reporting import SimpleHtmlReporter
from askui.speaker.askui_agent import AskUIAgent
from askui.speaker.conversation import Conversation
from askui.speaker.speaker import Speaker, SpeakerResult, Speakers
from askui.utils.caching.cache_manager import CacheManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Simple Custom Speaker with Approval Logic
# ============================================================================


class ApprovalSpeaker(Speaker):
    """Custom speaker that requires approval before executing certain actions.

    This speaker intercepts tool calls that match certain criteria and
    requests user approval before allowing them to proceed.
    """

    def __init__(self, tools_requiring_approval: list[str] | None = None) -> None:
        """Initialize the approval speaker.

        Args:
            tools_requiring_approval: List of tool names that require approval.
                If None, all tools require approval.
        """
        self.tools_requiring_approval = tools_requiring_approval
        self.pending_approval = False
        self.pending_message: MessageParam | None = None

    def get_name(self) -> str:
        """Return speaker name for identification."""
        return "ApprovalSpeaker"

    def can_handle(self, conversation: Conversation) -> bool:
        """Check if this speaker should handle the current step.

        This speaker handles assistant messages that contain tool calls
        requiring approval.
        """
        messages = conversation.get_messages()
        if not messages:
            return False

        last_message = messages[-1]

        # Check if last message is from assistant with tool calls
        if last_message.role != "assistant":
            return False

        if not last_message.content or not isinstance(last_message.content, list):
            return False

        # Check if any tool call requires approval
        for content_block in last_message.content:
            if (
                isinstance(content_block, dict)
                and content_block.get("type") == "tool_use"
            ):
                tool_name = content_block.get("name", "")
                if (
                    self.tools_requiring_approval is None
                    or tool_name in self.tools_requiring_approval
                ):
                    return True

        return False

    def handle_step(
        self, conversation: Conversation, cache_manager: CacheManager | None
    ) -> SpeakerResult:
        """Request approval for tool execution.

        Args:
            conversation: The conversation instance with current state
            cache_manager: Optional cache manager (not used in this example)

        Returns:
            SpeakerResult indicating whether to continue or switch speakers
        """
        messages = conversation.get_messages()
        last_message = messages[-1]

        # Extract tool calls that need approval
        tool_calls = []
        if isinstance(last_message.content, list):
            for content_block in last_message.content:
                if (
                    isinstance(content_block, dict)
                    and content_block.get("type") == "tool_use"
                ):
                    tool_name = content_block.get("name", "")
                    if (
                        self.tools_requiring_approval is None
                        or tool_name in self.tools_requiring_approval
                    ):
                        tool_calls.append(content_block)

        if not tool_calls:
            # No tools requiring approval, switch back to normal agent
            return SpeakerResult(status="switch_speaker", next_speaker="AskUIAgent")

        # Log approval request
        logger.info("=" * 60)
        logger.info("APPROVAL REQUIRED")
        logger.info("=" * 60)
        for tool_call in tool_calls:
            logger.info(f"Tool: {tool_call.get('name')}")
            logger.info(f"Input: {tool_call.get('input')}")
            logger.info("-" * 60)

        # In a real implementation, you would request user input here
        # For this example, we auto-approve
        logger.info("Auto-approving for demo purposes...")
        logger.info("=" * 60)

        # Switch back to AskUIAgent to continue normal flow
        return SpeakerResult(status="switch_speaker", next_speaker="AskUIAgent")


# ============================================================================
# Example 2: Logging Speaker that Monitors Conversation
# ============================================================================


class LoggingSpeaker(Speaker):
    """Custom speaker that logs conversation progress.

    This speaker intercepts all messages and logs them before passing
    control back to the main agent.
    """

    def __init__(self, log_file: str | None = None) -> None:
        """Initialize the logging speaker.

        Args:
            log_file: Optional file path to write logs to. If None, logs to console.
        """
        self.log_file = log_file
        self.message_count = 0

    def get_name(self) -> str:
        """Return speaker name for identification."""
        return "LoggingSpeaker"

    def can_handle(self, conversation: Conversation) -> bool:
        """This speaker can handle any conversation state for logging purposes."""
        # Only handle if there are new messages to log
        messages = conversation.get_messages()
        return len(messages) > self.message_count

    def handle_step(
        self, conversation: Conversation, cache_manager: CacheManager | None
    ) -> SpeakerResult:
        """Log new messages and switch back to main agent.

        Args:
            conversation: The conversation instance with current state
            cache_manager: Optional cache manager (not used in this example)

        Returns:
            SpeakerResult switching back to the main agent
        """
        messages = conversation.get_messages()

        # Log new messages
        while self.message_count < len(messages):
            message = messages[self.message_count]
            log_line = f"[Message {self.message_count + 1}] Role: {message.role}"

            if isinstance(message.content, str):
                log_line += f" | Content: {message.content[:100]}..."
            elif isinstance(message.content, list):
                log_line += f" | Blocks: {len(message.content)}"

            logger.info(log_line)
            self.message_count += 1

        # Switch back to main agent
        return SpeakerResult(status="switch_speaker", next_speaker="AskUIAgent")


# ============================================================================
# Example Tools for Demo
# ============================================================================


class SendEmailTool(Tool):
    """Example tool that simulates sending an email."""

    def __init__(self) -> None:
        super().__init__(
            name="send_email",
            description="Send an email to a recipient",
            input_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Email recipient"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"},
                },
                "required": ["to", "subject", "body"],
            },
        )

    def __call__(self, to: str, subject: str, body: str) -> str:
        logger.info(f"Sending email to {to}: {subject}")
        return f"Email sent successfully to {to}"


class CalculatorTool(Tool):
    """Example tool that performs calculations."""

    def __init__(self) -> None:
        super().__init__(
            name="calculator",
            description="Perform arithmetic calculations",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate",
                    },
                },
                "required": ["expression"],
            },
        )

    def __call__(self, expression: str) -> str:
        try:
            # Simple eval - in production use a proper math parser!
            result = eval(expression)  # noqa: S307
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"


# ============================================================================
# Demo Functions
# ============================================================================


def demo_approval_speaker() -> None:
    """Demonstrate using an approval speaker for sensitive operations."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 1: Approval Speaker")
    logger.info("=" * 80)

    goal = """
    Please use the send_email tool to send an email to user@example.com with:
    - Subject: "Test Email"
    - Body: "This is a test email from the custom speaker demo"
    """

    # Create speakers with approval requirement for email tool
    speakers = Speakers(
        {
            "ApprovalSpeaker": ApprovalSpeaker(tools_requiring_approval=["send_email"]),
            "AskUIAgent": AskUIAgent(),
        }
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_tools=[SendEmailTool(), CalculatorTool()],
    ) as agent:
        agent.act(goal, speakers=speakers)


def demo_logging_speaker() -> None:
    """Demonstrate using a logging speaker to monitor conversation."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: Logging Speaker")
    logger.info("=" * 80)

    goal = """
    Please perform the following calculations using the calculator tool:
    1. Calculate 15 + 27
    2. Calculate 100 - 45
    3. Calculate 8 * 7
    """

    # Create speakers with logging
    speakers = Speakers(
        {
            "LoggingSpeaker": LoggingSpeaker(),
            "AskUIAgent": AskUIAgent(),
        }
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_tools=[CalculatorTool()],
    ) as agent:
        agent.act(goal, speakers=speakers)


def demo_combined_speakers() -> None:
    """Demonstrate combining multiple custom speakers."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: Combined Speakers (Approval + Logging)")
    logger.info("=" * 80)

    goal = """
    Please:
    1. Calculate the sum of 25 + 35 using the calculator tool
    2. Send an email to admin@example.com with the result
    """

    # Combine multiple custom speakers
    speakers = Speakers(
        {
            "ApprovalSpeaker": ApprovalSpeaker(tools_requiring_approval=["send_email"]),
            "LoggingSpeaker": LoggingSpeaker(),
            "AskUIAgent": AskUIAgent(),
        }
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_tools=[SendEmailTool(), CalculatorTool()],
    ) as agent:
        agent.act(goal, speakers=speakers)


def demo_custom_settings_with_speakers() -> None:
    """Demonstrate passing custom settings along with speakers."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: Custom Settings with Speakers")
    logger.info("=" * 80)

    goal = """
    Please calculate 42 * 18 and explain your reasoning.
    """

    # Create custom settings
    custom_settings = ActSettings(
        messages=MessageSettings(
            system=ActSystemPrompt(
                system_capabilities="You are a helpful assistant that explains calculations step by step."
            ),
            thinking={"type": "enabled", "budget_tokens": 1024},
            temperature=1.0,
        ),
    )

    # Create speakers
    speakers = Speakers(
        {
            "LoggingSpeaker": LoggingSpeaker(),
            "AskUIAgent": AskUIAgent(),
        }
    )

    with VisionAgent(
        display=1,
        reporters=[SimpleHtmlReporter()],
        act_tools=[CalculatorTool()],
    ) as agent:
        agent.act(goal, speakers=speakers, settings=custom_settings)


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    # Run all demos
    # Note: These demos use simulated tools. In a real scenario with UI automation,
    # the speakers would work with actual screen interactions.

    print("\nCustom Speakers Demo")
    print("=" * 80)
    print("This demo shows how to create and use custom speakers with VisionAgent.")
    print("Custom speakers allow you to implement specialized conversation logic.")
    print("=" * 80)

    # Uncomment the demos you want to run:
    demo_approval_speaker()
    demo_logging_speaker()
    demo_combined_speakers()
    demo_custom_settings_with_speakers()

    print("\n" + "=" * 80)
    print("Demo completed!")
    print("=" * 80)
