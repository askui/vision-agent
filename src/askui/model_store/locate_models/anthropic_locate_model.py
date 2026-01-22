import json

from typing_extensions import override

from askui.locators.locators import Locator
from askui.locators.serializers import VlmLocatorSerializer
from askui.models.anthropic.messages_api import built_messages_for_get_and_locate
from askui.models.anthropic.settings import (
    AnthropicModelSettings,
    UnexpectedResponseError,
)
from askui.models.anthropic.utils import extract_click_coordinates
from askui.models.exceptions import ElementNotFoundError
from askui.models.models import LocateModel
from askui.models.shared.agent_message_param import (
    ContentBlockParam,
    TextBlockParam,
)
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.settings import LocateSettings
from askui.models.types.geometry import PointList
from askui.prompts.locate_prompts import build_system_prompt_locate
from askui.utils.image_utils import (
    ImageSource,
    scale_coordinates,
    scale_image_to_fit,
)


class AnthropicLocateModel(LocateModel):
    def __init__(
        self,
        model_id: str,
        settings: AnthropicModelSettings,
        messages_api: MessagesApi,
        locator_serializer: VlmLocatorSerializer,
    ) -> None:
        self._model_id = model_id
        self._settings = settings
        self._messages_api = messages_api
        self._locator_serializer = locator_serializer

    def _validate_content(self, content: list[ContentBlockParam]) -> None:
        """Validate that content is a single text block.

        Args:
            content (list[ContentBlockParam]): The content to validate

        Raises:
            UnexpectedResponseError: If content is not a single text block
        """
        if len(content) != 1 or content[0].type != "text":
            error_msg = "Unexpected response from Anthropic API"
            raise UnexpectedResponseError(error_msg, content)

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        locator_serialized = (
            self._locator_serializer.serialize(locator)
            if isinstance(locator, Locator)
            else locator
        )
        try:
            prompt = f"Click on {locator_serialized}"
            screen_width = self._settings.resolution[0]
            screen_height = self._settings.resolution[1]
            scaled_image = scale_image_to_fit(
                image.root,
                self._settings.resolution,
            )
            messages = built_messages_for_get_and_locate(scaled_image, prompt)
            system = build_system_prompt_locate(str(screen_width), str(screen_height))
            message = self._messages_api.create_message(
                messages=messages,
                model_id=self._model_id,
                system=system,
            )
            content: list[ContentBlockParam] = (
                message.content
                if isinstance(message.content, list)
                else [TextBlockParam(text=message.content)]
            )
            self._validate_content(content)
            content_text = content[0].text
            return [
                scale_coordinates(
                    extract_click_coordinates(content_text),
                    image.root.size,
                    self._settings.resolution,
                    inverse=True,
                )
            ]
        except (
            UnexpectedResponseError,
            ValueError,
            json.JSONDecodeError,
        ) as e:
            raise ElementNotFoundError(locator, locator_serialized) from e
