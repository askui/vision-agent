import platform
import sys
from datetime import datetime
from typing import Any, cast

import httpx
from anthropic.types.beta import (
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from typing_extensions import override

from askui.models.askui.settings import AskUiComputerAgentSettings
from askui.models.models import ActModel
from askui.reporting import Reporter
from askui.tools.agent_os import AgentOs
from askui.tools.anthropic import ComputerTool, ToolCollection, ToolResult
from askui.utils.str_utils import truncate_long_strings

from ...logger import logger

COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

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
* The current date is {datetime.today().strftime("%A, %B %d, %Y").replace(" 0", " ")}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""  # noqa: DTZ002, E501


def is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable error (status codes 429 or 529)."""
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in (429, 529)
    return False


class AskUiComputerAgent(ActModel):
    def __init__(
        self,
        agent_os: AgentOs,
        reporter: Reporter,
        settings: AskUiComputerAgentSettings,
    ) -> None:
        self._settings = settings
        self._reporter = reporter
        self._tool_collection = ToolCollection(
            ComputerTool(agent_os),
        )
        self._system = SYSTEM_PROMPT
        self._client = httpx.Client(
            base_url=f"{self._settings.askui.base_url}",
            headers={
                "Content-Type": "application/json",
                "Authorization": self._settings.askui.authorization_header,
            },
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=30, max=240),
        retry=retry_if_exception(is_retryable_error),
        reraise=True,
    )
    def step(self, messages: list[BetaMessageParam]) -> list[BetaMessageParam]:
        if self._settings.only_n_most_recent_images:
            self._maybe_filter_to_n_most_recent_images(
                messages,
                self._settings.only_n_most_recent_images,
                min_removal_threshold=self._settings.image_truncation_threshold,
            )

        try:
            request_body = {
                "max_tokens": self._settings.max_tokens,
                "messages": messages,
                "model": self._settings.model,
                "tools": self._tool_collection.to_params(),
                "betas": self._settings.betas,
                "system": [{"type": "text", "text": self._system}],
            }
            logger.debug(request_body)
            response = self._client.post(
                "/act/inference", json=request_body, timeout=300.0
            )
            response.raise_for_status()
            response_data = response.json()
            beta_message = BetaMessage.model_validate(response_data)
        except Exception as e:  # noqa: BLE001
            if is_retryable_error(e):
                logger.debug(e)
            raise

        response_params = self._response_to_params(beta_message)
        new_message: BetaMessageParam = {
            "role": "assistant",
            "content": response_params,
        }
        logger.debug(new_message)
        messages.append(new_message)
        if self._reporter is not None:
            self._reporter.add_message("AskUI Computer Use", response_params)

        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in response_params:
            if content_block["type"] == "tool_use":
                result = self._tool_collection.run(
                    name=content_block["name"],
                    tool_input=cast("dict[str, Any]", content_block["input"]),
                )
                tool_result_content.append(
                    self._make_api_tool_result(result, content_block["id"])
                )
        if len(tool_result_content) > 0:
            another_new_message: BetaMessageParam = {
                "content": tool_result_content,
                "role": "user",
            }
            logger.debug(
                truncate_long_strings(dict(another_new_message), max_length=200)
            )
            messages.append(another_new_message)
        return messages

    @override
    def act(self, goal: str, model_choice: str) -> None:
        messages: list[BetaMessageParam] = [{"role": "user", "content": goal}]
        logger.debug(messages[0])
        while messages[-1]["role"] == "user":
            messages = self.step(messages)

    @staticmethod
    def _maybe_filter_to_n_most_recent_images(
        messages: list,
        images_to_keep: int | None,
        min_removal_threshold: int,
    ) -> list | None:
        """
        With the assumption that images are screenshots that are of diminishing value as
        the conversation progresses, remove all but the final `images_to_keep` tool_result
        images in place, with a chunk of min_removal_threshold to reduce the amount we
        break the implicit prompt cache.
        """  # noqa: E501
        if images_to_keep is None:
            return messages

        tool_result_blocks = [
            item
            for message in messages
            for item in (
                message["content"] if isinstance(message["content"], list) else []
            )
            if isinstance(item, dict) and item.get("type") == "tool_result"
        ]
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
        return None

    @staticmethod
    def _response_to_params(
        response: BetaMessage,
    ) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
        res: list[BetaTextBlockParam | BetaToolUseBlockParam] = []
        for block in response.content:
            if isinstance(block, BetaTextBlock):
                res.append({"type": "text", "text": block.text})
            else:
                res.append(cast("BetaToolUseBlockParam", block.model_dump()))
        return res

    def _make_api_tool_result(
        self, result: ToolResult, tool_use_id: str
    ) -> BetaToolResultBlockParam:
        """Convert an agent ToolResult to an API ToolResultBlockParam."""
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
        if result.system:
            result_text = f"<system>{result.system}</system>\n{result_text}"
        return result_text
