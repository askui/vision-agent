import json
from typing import Type

import anthropic
from typing_extensions import override

from askui.exceptions import (
    ElementNotFoundError,
    QueryNoResponseError,
    QueryUnexpectedResponseError,
)
from askui.locators.locators import Locator
from askui.locators.serializers import VlmLocatorSerializer
from askui.logger import logger
from askui.models.anthropic.settings import ClaudeSettings
from askui.models.models import (
    ANTHROPIC_MODEL_NAME_MAPPING,
    GetModel,
    LocateModel,
    ModelComposition,
    ModelName,
    Point,
)
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import (
    ImageSource,
    image_to_base64,
    scale_coordinates_back,
    scale_image_with_padding,
)

from .utils import extract_click_coordinates


class ClaudeHandler(LocateModel, GetModel):
    def __init__(
        self, settings: ClaudeSettings, locator_serializer: VlmLocatorSerializer
    ) -> None:
        self._settings = settings
        self._client = anthropic.Anthropic(
            api_key=self._settings.anthropic.api_key.get_secret_value()
        )
        self._locator_serializer = locator_serializer

    def _inference(
        self, base64_image: str, prompt: str, system_prompt: str, model: str
    ) -> list[anthropic.types.ContentBlock]:
        message = self._client.messages.create(
            model=model,
            max_tokens=self._settings.max_tokens,
            temperature=self._settings.temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return message.content

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        if not isinstance(model_choice, str):
            error_msg = "Model composition is not supported for Claude"
            raise NotImplementedError(error_msg)
        locator_serialized = (
            self._locator_serializer.serialize(locator)
            if isinstance(locator, Locator)
            else locator
        )
        prompt = f"Click on {locator_serialized}"
        screen_width = self._settings.resolution[0]
        screen_height = self._settings.resolution[1]
        system_prompt = f"Use a mouse and keyboard to interact with a computer, and take screenshots.\n* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.\n* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try taking another screenshot.\n* The screen's resolution is {screen_width}x{screen_height}.\n* The display number is 0\n* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.\n* If you tried clicking on a program or link but it failed to load, even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.\n* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.\n"  # noqa: E501
        scaled_image = scale_image_with_padding(image.root, screen_width, screen_height)
        response = self._inference(
            image_to_base64(scaled_image),
            prompt,
            system_prompt,
            model=ANTHROPIC_MODEL_NAME_MAPPING[ModelName(model_choice)],
        )
        assert len(response) > 0
        r = response[0]
        assert r.type == "text"
        logger.debug("ClaudeHandler received locator: %s", r.text)
        try:
            scaled_x, scaled_y = extract_click_coordinates(r.text)
        except (ValueError, json.JSONDecodeError) as e:
            raise ElementNotFoundError(locator, locator_serialized) from e
        x, y = scale_coordinates_back(
            scaled_x,
            scaled_y,
            image.root.width,
            image.root.height,
            screen_width,
            screen_height,
        )
        return int(x), int(y)

    @override
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        if response_schema is not None:
            error_msg = "Response schema is not yet supported for Claude"
            raise NotImplementedError(error_msg)
        scaled_image = scale_image_with_padding(
            image=image.root,
            max_width=self._settings.resolution[0],
            max_height=self._settings.resolution[1],
        )
        system_prompt = "You are an agent to process screenshots and answer questions about things on the screen or extract information from it. Answer only with the response to the question and keep it short and precise."  # noqa: E501
        response = self._inference(
            base64_image=image_to_base64(scaled_image),
            prompt=query,
            system_prompt=system_prompt,
            model=ANTHROPIC_MODEL_NAME_MAPPING[ModelName(model_choice)],
        )
        if len(response) == 0:
            error_msg = f"No response from Claude to query: {query}"
            raise QueryNoResponseError(error_msg, query)
        r = response[0]
        if r.type == "text":
            return r.text
        error_msg = f"Unexpected response from Claude: {r}"
        raise QueryUnexpectedResponseError(error_msg, query, r)
