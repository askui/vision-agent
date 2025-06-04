import platform
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Callable, Generic, cast

from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)
from pydantic import BaseModel, Field
from typing_extensions import TypeVar

from askui.models.models import ActModel
from askui.reporting import Reporter
from askui.tools.agent_os import AgentOs
from askui.tools.anthropic import ComputerTool, ToolCollection, ToolResult

from ...logger import logger

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"

PC_KEY = [
    "backspace",
    "delete",
    "enter",
    "tab",
    "escape",
    "up",
    "down",
    "right",
    "left",
    "home",
    "end",
    "pageup",
    "pagedown",
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
    "f11",
    "f12",
    "space",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "!",
    '"',
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    "+",
    ",",
    "-",
    ".",
    "/",
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    "[",
    "\\",
    "]",
    "^",
    "_",
    "`",
    "{",
    "|",
    "}",
    "~",
]

SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* You are utilising a {sys.platform} machine using {platform.machine()} architecture with internet access.
* When asked to perform web tasks try to open the browser (firefox, chrome, safari, ...) if not already open. Often you can find the browser icons in the toolbars of the operating systems.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* Valid keyboard keys available are {", ".join(PC_KEY)}
* The current date is {datetime.now(timezone.utc).strftime("%A, %B %d, %Y").replace(" 0", " ")}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""  # noqa: DTZ002, E501


class ComputerAgentSettingsBase(BaseModel):
    """Settings for computer agents."""

    max_tokens: int = 4096
    only_n_most_recent_images: int = 3
    image_truncation_threshold: int = 10
    betas: list[str] = Field(default_factory=lambda: [COMPUTER_USE_BETA_FLAG])


ComputerAgentSettings = TypeVar(
    "ComputerAgentSettings", bound=ComputerAgentSettingsBase
)


class ComputerAgent(ActModel, ABC, Generic[ComputerAgentSettings]):
    """Base class for computer agents that can execute autonomous actions.

    This class provides common functionality for both AskUI and Anthropic
    computer agents,
    including tool handling, message processing, and image filtering.
    """

    def __init__(
        self,
        settings: ComputerAgentSettings,
        agent_os: AgentOs,
        reporter: Reporter,
    ) -> None:
        """Initialize the computer agent.

        Args:
            settings (ComputerAgentSettings): The settings for the computer agent.
            agent_os (AgentOs): The operating system agent for executing commands.
            reporter (Reporter): The reporter for logging messages and actions.
        """
        self._settings = settings
        self._reporter = reporter
        self._tool_collection = ToolCollection(
            ComputerTool(agent_os),
        )
        self._system = BetaTextBlockParam(
            type="text",
            text=f"{SYSTEM_PROMPT}",
        )

    @abstractmethod
    def _create_message(
        self, messages: list[BetaMessageParam], model_choice: str
    ) -> BetaMessage:
        """Create a message using the agent's API.

        Args:
            messages (list[BetaMessageParam]): The message history.
            model_choice (str): The model to use for message creation.

        Returns:
            BetaMessage: The created message.
        """
        raise NotImplementedError

    def _step(
        self,
        messages: list[BetaMessageParam],
        model_choice: str,
        on_message: Callable[
            [BetaMessageParam, list[BetaMessageParam]], BetaMessageParam | None
        ]
        | None = None,
        on_tool_result: Callable[
            [ToolResult, BetaToolUseBlockParam, list[BetaMessageParam]],
            ToolResult | None,
        ]
        | None = None,
    ) -> None:
        """Execute a single step in the conversation.

        Args:
            messages (list[BetaMessageParam]): The message history.
            model_choice (str): The model to use for message creation.
            on_message (Callable, optional): Callback for message processing.
            on_tool_result (Callable, optional): Callback for tool result processing.

        Returns:
            None
        """
        if self._settings.only_n_most_recent_images:
            self._maybe_filter_to_n_most_recent_images(
                messages,
                self._settings.only_n_most_recent_images,
                min_removal_threshold=self._settings.image_truncation_threshold,
            )
        response_message = self._create_message(messages, model_choice)
        response_message_param: BetaMessageParam = cast(
            "BetaMessageParam",
            response_message.model_dump(include={"content", "role"}),
        )
        message_by_assistant = self._call_on_message(
            on_message, response_message_param, messages
        )
        if message_by_assistant is None:
            return
        logger.debug(message_by_assistant)
        messages.append(message_by_assistant)
        self._reporter.add_message(self.__class__.__name__, dict(message_by_assistant))
        if tool_result_message := self._use_tools(
            response_message, messages, on_tool_result
        ):
            if tool_result_message := self._call_on_message(
                on_message, tool_result_message, messages
            ):
                messages.append(tool_result_message)
                self._step(
                    messages=messages,
                    model_choice=model_choice,
                    on_message=on_message,
                    on_tool_result=on_tool_result,
                )

    def _call_on_message(
        self,
        on_message: Callable[
            [BetaMessageParam, list[BetaMessageParam]], BetaMessageParam | None
        ]
        | None,
        message: BetaMessageParam,
        messages: list[BetaMessageParam],
    ) -> BetaMessageParam | None:
        if on_message is None:
            return message
        return on_message(message, messages)

    def act(
        self,
        messages: list[BetaMessageParam],
        model_choice: str,
        on_message: Callable[
            [BetaMessageParam, list[BetaMessageParam]], BetaMessageParam | None
        ]
        | None = None,
        on_tool_result: Callable[
            [ToolResult, BetaToolUseBlockParam, list[BetaMessageParam]],
            ToolResult | None,
        ]
        | None = None,
    ) -> None:
        logger.debug(messages[0])
        self._step(
            messages=messages,
            model_choice=model_choice,
            on_message=on_message,
            on_tool_result=on_tool_result,
        )

    def _use_tools(
        self,
        message: BetaMessage,
        messages: list[BetaMessageParam],
        on_tool_result: Callable[
            [ToolResult, BetaToolUseBlockParam, list[BetaMessageParam]],
            ToolResult | None,
        ]
        | None = None,
    ) -> BetaMessageParam | None:
        """Process tool use blocks in a message.

        Args:
            message (BetaMessage): The message containing tool use blocks.
            messages (list[BetaMessageParam]): The message history.
            on_tool_result (Callable, optional): Callback for tool result processing.

        Returns:
            BetaMessageParam | None: A message containing tool results or `None`
                if no tools were used.
        """
        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in message.content:
            if content_block.type == "tool_use":
                result = self._tool_collection.run(
                    name=content_block.name,
                    tool_input=content_block.input,  # type: ignore[arg-type]
                )
                if on_tool_result is not None:
                    content_block_param = cast(
                        "BetaToolUseBlockParam", content_block.model_dump()
                    )
                    result_cb = on_tool_result(result, content_block_param, messages)
                    if result_cb is None:
                        return None
                    result = result_cb
                tool_result_content.append(
                    self._make_api_tool_result(result, content_block.id)
                )
        if len(tool_result_content) > 0:
            tool_result_message: BetaMessageParam = {
                "content": tool_result_content,
                "role": "user",
            }
            logger.debug(tool_result_message)
            return tool_result_message
        return None

    @staticmethod
    def _maybe_filter_to_n_most_recent_images(
        messages: list[BetaMessageParam],
        images_to_keep: int | None,
        min_removal_threshold: int,
    ) -> list[BetaMessageParam] | None:
        """Filter messages to keep only the most recent images.

        Args:
            messages (list[BetaMessageParam]): The message history.
            images_to_keep (int | None): Number of most recent images to keep.
            min_removal_threshold (int): Minimum number of images to remove at once.

        Returns:
            list[BetaMessageParam] | None: The filtered message history or `None` if no
                filtering was done.
        """
        if images_to_keep is None:
            return messages

        tool_result_blocks = cast(
            "list[BetaToolResultBlockParam]",
            [
                item
                for message in messages
                for item in (
                    message["content"] if isinstance(message["content"], list) else []
                )
                if item.get("type") == "tool_result"
            ],
        )
        total_images = sum(
            1
            for tool_result in tool_result_blocks
            for content in tool_result.get("content", [])
            if isinstance(content, dict) and content.get("type") == "image"
        )
        images_to_remove = total_images - images_to_keep
        # for better cache behavior, we want to remove in chunks
        images_to_remove -= images_to_remove % min_removal_threshold
        for tool_result in tool_result_blocks:
            if isinstance(tool_result.get("content"), list):
                new_content: list[BetaContentBlockParam] = []
                for content in tool_result.get("content", []):
                    if isinstance(content, dict) and content.get("type") == "image":
                        if images_to_remove > 0:
                            images_to_remove -= 1
                            continue
                    new_content.append(cast("BetaContentBlockParam", content))
                tool_result["content"] = new_content  # type: ignore[typeddict-item]
        return None

    def _make_api_tool_result(
        self, result: ToolResult, tool_use_id: str
    ) -> BetaToolResultBlockParam:
        """Convert a tool result to an API tool result block.

        Args:
            result (ToolResult): The tool result to convert.
            tool_use_id (str): The ID of the tool use block.

        Returns:
            BetaToolResultBlockParam: The API tool result block.
        """
        tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
        is_error = False
        if result.error:
            is_error = True
            tool_result_content = self._maybe_prepend_system_tool_result(
                result, result.error
            )
        else:
            assert isinstance(tool_result_content, list)
            if result.output:
                tool_result_content.append(
                    {
                        "type": "text",
                        "text": self._maybe_prepend_system_tool_result(
                            result, result.output
                        ),
                    }
                )
            if result.base64_image:
                tool_result_content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": result.base64_image,
                        },
                    }
                )
        return {
            "type": "tool_result",
            "content": tool_result_content,
            "tool_use_id": tool_use_id,
            "is_error": is_error,
        }

    @staticmethod
    def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str) -> str:
        """Prepend system message to tool result text if available.

        Args:
            result (ToolResult): The tool result.
            result_text (str): The result text.

        Returns:
            str: The result text with optional system message prepended.
        """
        if result.system:
            result_text = f"<system>{result.system}</system>\n{result_text}"
        return result_text
