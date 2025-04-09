import sys
import platform
from datetime import datetime
from typing import Any, cast, Literal

from anthropic import (
    Anthropic,
    APIError,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

from ...tools.anthropic import ComputerTool, ToolCollection, ToolResult
from ...logging import logger
from ...utils import truncate_long_strings
from askui.reporting.report import SimpleReportGenerator


COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
PC_KEY = Literal['backspace', 'delete', 'enter', 'tab', 'escape', 'up', 'down', 'right', 'left', 'home', 'end', 'pageup', 'pagedown', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'space', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~']


# class APIProvider(StrEnum):
#     ANTHROPIC = "anthropic"
#     BEDROCK = "bedrock"
#     VERTEX = "vertex"


# PROVIDER_TO_DEFAULT_MODEL_NAME: dict[APIProvider, str] = {
#     APIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
#     APIProvider.BEDROCK: "anthropic.claude-3-5-sonnet-20241022-v2:0",
#     APIProvider.VERTEX: "claude-3-5-sonnet-v2@20241022",
# }


SYSTEM_PROMPT = f"""<SYSTEM_CAPABILITY>
* Based on the screen context, determine if the environment is a **desktop system** (e.g., Windows, macOS, Linux) or an **Android device**.
* If it's a **desktop system** (detected via visible window borders, taskbars, mouse cursor, browser UI, etc.):
  - You are utilizing a {sys.platform} machine using {platform.machine()} architecture with internet access.
  - When performing web tasks, open a browser (Firefox, Chrome, Safari, etc.) if not already open.
  - You may zoom out or scroll down to see full webpage content.
  - Chain function calls where possible to reduce delays.
  - Valid keyboard keys include: {', '.join(list(PC_KEY.__args__))}

* If it's an **Android device** (detected via mobile UI layout, app icons, navigation buttons, mobile keyboard prompts, etc.):
  - You are interacting with an Android device.
  - Your actions are limited to **screen taps (clicks)** and **mouse movements** — no keyboard input.
  - Navigate apps using visible buttons (e.g., Back, Home, Menu), tap icons, and simulate swipe gestures to scroll.

* In either case, visually inspect the entire screen before deciding something isn’t available.
* The current date is {datetime.today().strftime('%A, %B %d, %Y').replace(' 0', ' ')}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* If using Firefox on desktop and a startup wizard appears, IGNORE IT completely. Do not click "skip this step." Instead, click the address bar directly and enter a URL or search term.
* If viewing a PDF on desktop, and it seems like you’ll need the whole document:
  - Extract the URL, use `curl` to download it, and convert it with `pdftotext`.
* On Android, remember you cannot use keyboard input. Use visible on-screen options on-screen keyboards, or navigation alternatives.
* Always prefer interacting with **visible UI elements** — skip, close, or proceed through wizards or onboarding flows where possible.
</IMPORTANT>"""


class ClaudeComputerAgent:
    def __init__(self, controller_client, report: SimpleReportGenerator | None = None) -> None:
        self.report = report
        self.tool_collection = ToolCollection(
            ComputerTool(controller_client),
        )
        self.system = BetaTextBlockParam(
            type="text",
            text=f"{SYSTEM_PROMPT}",
        )
        self.enable_prompt_caching = False
        self.betas = [COMPUTER_USE_BETA_FLAG]
        self.image_truncation_threshold = 10
        self.only_n_most_recent_images = 3
        self.max_tokens = 4096
        self.client = Anthropic()
        self.model = "claude-3-5-sonnet-20241022"

    def step(self, messages: list):
        if self.only_n_most_recent_images:
            self._maybe_filter_to_n_most_recent_images(
                messages,
                self.only_n_most_recent_images,
                min_removal_threshold=self.image_truncation_threshold,
            )

        try:
            raw_response = self.client.beta.messages.with_raw_response.create(
                max_tokens=self.max_tokens,
                messages=messages,
                model=self.model,
                system=[self.system],
                tools=self.tool_collection.to_params(),
                betas=self.betas,
            )
        except (APIStatusError, APIResponseValidationError) as e:
            logger.error(e)
            return messages
        except APIError as e:
            logger.error(e)
            return messages
        
        response = raw_response.parse()
        response_params = self._response_to_params(response)
        new_message = {
            "role": "assistant",
            "content": response_params,
        }
        logger.debug(new_message)
        messages.append(new_message)
        if self.report is not None: 
            self.report.add_message("Anthropic Computer Use", response_params)

        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in response_params:
            if content_block["type"] == "tool_use":
                result = self.tool_collection.run(
                    name=content_block["name"],
                    tool_input=cast(dict[str, Any], content_block["input"]),
                )
                tool_result_content.append(
                    self._make_api_tool_result(result, content_block["id"])
                )
        if len(tool_result_content) > 0:
            new_message = {"content": tool_result_content, "role": "user"}
            logger.debug(truncate_long_strings(new_message, max_length=200))
            messages.append(new_message)
        return messages

    
    def run(self, goal: str):
        messages = [{"role": "user", "content": goal}]
        logger.debug(messages[0])
        while messages[-1]["role"] == "user":
            messages = self.step(messages)


    @staticmethod
    def _maybe_filter_to_n_most_recent_images(
        messages: list[BetaMessageParam],
        images_to_keep: int,
        min_removal_threshold: int,
    ):
        """
        With the assumption that images are screenshots that are of diminishing value as
        the conversation progresses, remove all but the final `images_to_keep` tool_result
        images in place, with a chunk of min_removal_threshold to reduce the amount we
        break the implicit prompt cache.
        """
        if images_to_keep is None:
            return messages

        tool_result_blocks = cast(
            list[BetaToolResultBlockParam],
            [
                item
                for message in messages
                for item in (
                    message["content"] if isinstance(message["content"], list) else []
                )
                if isinstance(item, dict) and item.get("type") == "tool_result"
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
                new_content = []
                for content in tool_result.get("content", []):
                    if isinstance(content, dict) and content.get("type") == "image":
                        if images_to_remove > 0:
                            images_to_remove -= 1
                            continue
                    new_content.append(content)
                tool_result["content"] = new_content

    @staticmethod
    def _response_to_params(
        response: BetaMessage,
    ) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
        res: list[BetaTextBlockParam | BetaToolUseBlockParam] = []
        for block in response.content:
            if isinstance(block, BetaTextBlock):
                res.append({"type": "text", "text": block.text})
            else:
                res.append(cast(BetaToolUseBlockParam, block.model_dump()))
        return res

    @staticmethod
    def _inject_prompt_caching(
        messages: list[BetaMessageParam],
    ):
        """
        Set cache breakpoints for the 3 most recent turns
        one cache breakpoint is left for tools/system prompt, to be shared across sessions
        """

        breakpoints_remaining = 3
        for message in reversed(messages):
            if message["role"] == "user" and isinstance(
                content := message["content"], list
            ):
                if breakpoints_remaining:
                    breakpoints_remaining -= 1
                    content[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                        {"type": "ephemeral"}
                    )
                else:
                    content[-1].pop("cache_control", None)
                    # we'll only every have one extra turn per loop
                    break

    def _make_api_tool_result(
        self, result: ToolResult, tool_use_id: str
    ) -> BetaToolResultBlockParam:
        """Convert an agent ToolResult to an API ToolResultBlockParam."""
        tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
        is_error = False
        if result.error:
            is_error = True
            tool_result_content = self._maybe_prepend_system_tool_result(result, result.error)
        else:
            if result.output:
                tool_result_content.append(
                    {
                        "type": "text",
                        "text": self._maybe_prepend_system_tool_result(result, result.output),
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
    def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
        if result.system:
            result_text = f"<system>{result.system}</system>\n{result_text}"
        return result_text
