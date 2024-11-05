import sys
import platform
from datetime import datetime
from typing import Any, cast, Literal

from anthropic import (
    Anthropic,
    AnthropicBedrock,
    AnthropicVertex,
    APIError,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaContentBlockParam,
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
* You are utilising a {sys.platform} machine using {platform.machine()} architecture with internet access.
* When asked to perform web tasks try to open the browser (firefox, chrome, safari, ...) if not already open. Often you can find the browser icons in the toolbars of the operating systems.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* Valid keyboard keys available are {', '.join(list(PC_KEY.__args__))}
* The current date is {datetime.today().strftime('%A, %B %d, %Y').replace(' 0', ' ')}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""


class ClaudeComputerAgent:
    def __init__(self, controller_client):
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

    
    def run(self, instruction: str):
        messages = [{"role": "user", "content": instruction}]
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
