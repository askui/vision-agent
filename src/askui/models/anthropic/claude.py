import json

import anthropic
from PIL import Image

from askui.exceptions import (
    ElementNotFoundError,
    QueryNoResponseError,
    QueryUnexpectedResponseError,
)
from askui.logger import logger
from askui.models.anthropic.settings import ClaudeSettings
from askui.utils.image_utils import (
    ImageSource,
    image_to_base64,
    scale_coordinates_back,
    scale_image_with_padding,
)

from .utils import extract_click_coordinates


class ClaudeHandler:
    def __init__(self, settings: ClaudeSettings) -> None:
        self._settings = settings
        self._client = anthropic.Anthropic(
            api_key=self._settings.anthropic.api_key.get_secret_value()
        )

    def _inference(
        self, base64_image: str, prompt: str, system_prompt: str
    ) -> list[anthropic.types.ContentBlock]:
        message = self._client.messages.create(
            model=self._settings.model,
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

    def locate_inference(self, image: Image.Image, locator: str) -> tuple[int, int]:
        prompt = f"Click on {locator}"
        screen_width = self._settings.resolution[0]
        screen_height = self._settings.resolution[1]
        system_prompt = f"Use a mouse and keyboard to interact with a computer, and take screenshots.\n* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.\n* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try taking another screenshot.\n* The screen's resolution is {screen_width}x{screen_height}.\n* The display number is 0\n* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.\n* If you tried clicking on a program or link but it failed to load, even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.\n* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.\n"  # noqa: E501
        scaled_image = scale_image_with_padding(image, screen_width, screen_height)
        response = self._inference(image_to_base64(scaled_image), prompt, system_prompt)
        assert len(response) > 0
        r = response[0]
        assert r.type == "text"
        logger.debug("ClaudeHandler received locator: %s", r.text)
        try:
            scaled_x, scaled_y = extract_click_coordinates(r.text)
        except (ValueError, json.JSONDecodeError) as e:
            error_msg = f"Element not found: {locator}"
            raise ElementNotFoundError(error_msg) from e
        x, y = scale_coordinates_back(
            scaled_x, scaled_y, image.width, image.height, screen_width, screen_height
        )
        return int(x), int(y)

    def get_inference(self, image: ImageSource, query: str) -> str:
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
        )
        if len(response) == 0:
            error_msg = f"No response from Claude to query: {query}"
            raise QueryNoResponseError(error_msg, query)
        r = response[0]
        if r.type == "text":
            return r.text
        error_msg = f"Unexpected response from Claude: {r}"
        raise QueryUnexpectedResponseError(error_msg, query, r)
