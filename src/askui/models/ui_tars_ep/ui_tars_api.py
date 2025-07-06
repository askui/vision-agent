import math
import re
import time
from typing import Any, Type

from openai import OpenAI
from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings
from typing_extensions import override

from askui.locators.locators import Locator
from askui.locators.serializers import VlmLocatorSerializer
from askui.models.exceptions import ElementNotFoundError, QueryNoResponseError
from askui.models.models import ActModel, GetModel, LocateModel, ModelComposition, Point
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import Tool
from askui.models.types.response_schemas import ResponseSchema
from askui.reporting import Reporter
from askui.tools.agent_os import AgentOs
from askui.utils.image_utils import ImageSource, image_to_base64

from .parser import UITarsEPMessage
from .prompts import PROMPT, PROMPT_QA

# Constants copied from vision_processing.py in package qwen_vl_utils
# See also github.com/bytedance/UI-TARS/blob/main/README_coordinates.md
IMAGE_FACTOR = 28
MIN_PIXELS = 100 * 28 * 28  #  4 * 28 * 28 in the original vision_processing.py
MAX_PIXELS = 16384 * 28 * 28
MAX_RATIO = 200


def round_by_factor(number: int, factor: int) -> int:
    """Returns the closest integer to 'number' that is divisible by 'factor'."""
    return round(number / factor) * factor


def ceil_by_factor(number: float, factor: int) -> int:
    """Returns the smallest integer greater than or equal to 'number' that is divisible by 'factor'."""
    return math.ceil(number / factor) * factor


def floor_by_factor(number: float, factor: int) -> int:
    """Returns the largest integer less than or equal to 'number' that is divisible by 'factor'."""
    return math.floor(number / factor) * factor


@staticmethod
def smart_resize(
    height: int,
    width: int,
    factor: int = IMAGE_FACTOR,
    min_pixels: int = MIN_PIXELS,
    max_pixels: int = MAX_PIXELS,
) -> tuple[int, int]:
    """
    Rescales the image so that the following conditions are met (see github.com/bytedance/UI-TARS/blob/main/README_coordinates.md):

    1. Both dimensions (height and width) are divisible by 'factor'.

    2. The total number of pixels is within the range ['min_pixels', 'max_pixels'].

    3. The aspect ratio of the image is maintained as closely as possible.
    """
    if max(height, width) / min(height, width) > MAX_RATIO:
        error_msg = f"absolute aspect ratio must be smaller than {MAX_RATIO}, got {max(height, width) / min(height, width)}"
        raise ValueError(error_msg)
    h_bar = max(factor, round_by_factor(height, factor))
    w_bar = max(factor, round_by_factor(width, factor))
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = floor_by_factor(height / beta, factor)
        w_bar = floor_by_factor(width / beta, factor)
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = ceil_by_factor(height * beta, factor)
        w_bar = ceil_by_factor(width * beta, factor)
    return h_bar, w_bar


class UiTarsApiHandlerSettings(BaseSettings):
    """Settings for TARS API."""

    tars_url: HttpUrl = Field(
        validation_alias="TARS_URL",
    )
    tars_api_key: SecretStr = Field(
        min_length=1,
        validation_alias="TARS_API_KEY",
    )


class UiTarsApiHandler(ActModel, LocateModel, GetModel):
    def __init__(
        self,
        agent_os: AgentOs,
        reporter: Reporter,
        settings: UiTarsApiHandlerSettings,
        locator_serializer: VlmLocatorSerializer,
    ) -> None:
        self._agent_os = agent_os
        self._reporter = reporter
        self._settings = settings
        self._client = OpenAI(
            api_key=self._settings.tars_api_key.get_secret_value(),
            base_url=str(self._settings.tars_url),
        )
        self._locator_serializer = locator_serializer

    def _predict(self, image_url: str, instruction: str, prompt: str) -> str | None:
        chat_completion = self._client.chat.completions.create(
            model="tgi",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                        {"type": "text", "text": prompt + instruction},
                    ],
                }
            ],
            top_p=None,
            temperature=None,
            max_tokens=150,
            stream=False,
            seed=None,
            stop=None,
            frequency_penalty=None,
            presence_penalty=None,
        )
        return chat_completion.choices[0].message.content

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        if not isinstance(model_choice, str):
            error_msg = "Model composition is not supported for UI-TARS"
            raise NotImplementedError(error_msg)
        locator_serialized = (
            self._locator_serializer.serialize(locator)
            if isinstance(locator, Locator)
            else locator
        )
        askui_locator = f'Click on "{locator_serialized}"'
        prediction = self._predict(
            image_url=image.to_data_url(),
            instruction=askui_locator,
            prompt=PROMPT,
        )
        assert prediction is not None
        pattern = r"click\(start_box='(\(\d+,\d+\))'\)"
        match = re.search(pattern, prediction)
        if match:
            x, y = match.group(1).strip("()").split(",")
            x, y = int(x), int(y)
            width, height = image.root.size
            new_height, new_width = smart_resize(height, width)
            x, y = (int(x / new_width * width), int(y / new_height * height))
            return x, y
        raise ElementNotFoundError(locator, locator_serialized)

    @override
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        if response_schema is not None:
            error_msg = f'Response schema is not supported for model "{model_choice}"'
            raise NotImplementedError(error_msg)
        response = self._predict(
            image_url=image.to_data_url(),
            instruction=query,
            prompt=PROMPT_QA,
        )
        if response is None:
            error_msg = f'No response from model "{model_choice}" to query: "{query}"'
            raise QueryNoResponseError(error_msg, query)
        return response

    @override
    def act(
        self,
        messages: list[MessageParam],
        model_choice: str,
        on_message: OnMessageCb | None = None,
        tools: list[Tool] | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        if on_message is not None:
            error_msg = "on_message is not supported for UI-TARS"
            raise NotImplementedError(error_msg)
        if len(messages) != 1:
            error_msg = "UI-TARS only supports one message"
            raise ValueError(error_msg)
        message = messages[0]
        if message.role != "user":
            error_msg = "UI-TARS only supports user messages"
            raise ValueError(error_msg)
        if not isinstance(message.content, str):
            error_msg = "UI-TARS only supports text messages"
            raise ValueError(error_msg)  # noqa: TRY004
        goal = message.content
        screenshot = self._agent_os.screenshot()
        self.act_history = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:image/png;base64,{image_to_base64(screenshot)}"
                            )
                        },
                    },
                    {"type": "text", "text": PROMPT + goal},
                ],
            }
        ]
        self.execute_act(self.act_history)

    def add_screenshot_to_history(self, message_history: list[dict[str, Any]]) -> None:
        screenshot = self._agent_os.screenshot()
        message_history.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:image/png;base64,{image_to_base64(screenshot)}"
                            )
                        },
                    }
                ],
            }
        )

    def filter_message_thread(
        self, message_history: list[dict[str, Any]], max_screenshots: int = 3
    ) -> list[dict[str, Any]]:
        """
        Filter message history to keep only the last n screenshots while preserving all text content.

        Args:
            message_history: List of message dictionaries
            max_screenshots: Maximum number of screenshots to keep (default: 5)
        """
        # Count screenshots from the end to keep track of the most recent ones
        screenshot_count = 0
        filtered_messages: list[dict[str, Any]] = []

        # Iterate through messages in reverse to keep the most recent screenshots
        for message in reversed(message_history):
            content = message["content"]

            if isinstance(content, list):
                # Check if message contains an image
                has_image = any(item.get("type") == "image_url" for item in content)

                if has_image:
                    screenshot_count += 1
                    if screenshot_count <= max_screenshots:
                        filtered_messages.insert(0, message)
                    else:
                        # Keep only text content if screenshot limit exceeded
                        text_content = [
                            item for item in content if item.get("type") == "text"
                        ]
                        if text_content:
                            filtered_messages.insert(
                                0, {"role": message["role"], "content": text_content}
                            )
                else:
                    filtered_messages.insert(0, message)
            else:
                filtered_messages.insert(0, message)

        return filtered_messages

    def execute_act(self, message_history: list[dict[str, Any]]) -> None:
        message_history = self.filter_message_thread(message_history)

        chat_completion = self._client.chat.completions.create(
            model="tgi",
            messages=message_history,
            top_p=None,
            temperature=None,
            max_tokens=150,
            stream=False,
            seed=None,
            stop=None,
            frequency_penalty=None,
            presence_penalty=None,
        )
        raw_message = chat_completion.choices[-1].message.content
        print(raw_message)

        if self._reporter is not None:
            self._reporter.add_message("UI-TARS", raw_message)

        try:
            message = UITarsEPMessage.parse_message(raw_message)
            print(message)
        except Exception as e:  # noqa: BLE001 - We want to catch all other exceptions here
            message_history.append(
                {"role": "user", "content": [{"type": "text", "text": str(e)}]}
            )
            self.execute_act(message_history)
            return

        action = message.parsed_action
        if action.action_type == "click":
            self._agent_os.mouse_move(action.start_box.x, action.start_box.y)
            self._agent_os.click("left")
            time.sleep(1)
        if action.action_type == "type":
            self._agent_os.click("left")
            self._agent_os.type(action.content)
            time.sleep(0.5)
        if action.action_type == "hotkey":
            self._agent_os.keyboard_pressed(action.key)
            self._agent_os.keyboard_release(action.key)
            time.sleep(0.5)
        if action.action_type == "call_user":
            time.sleep(1)
        if action.action_type == "wait":
            time.sleep(2)
        if action.action_type == "finished":
            return

        self.add_screenshot_to_history(message_history)
        self.execute_act(message_history)

    def _filter_messages(
        self, messages: list[UITarsEPMessage], max_messages: int
    ) -> list[UITarsEPMessage]:
        return messages[-max_messages:]
