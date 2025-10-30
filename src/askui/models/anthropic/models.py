import json
from typing import Type, cast

from pydantic import Field
from pydantic_settings import BaseSettings
from typing_extensions import override

from askui.locators.locators import Locator
from askui.locators.serializers import VlmLocatorSerializer
from askui.models.exceptions import (
    ElementNotFoundError,
    QueryNoResponseError,
    QueryUnexpectedResponseError,
)
from askui.models.models import GetModel, LocateModel, ModelComposition, PointList
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
)
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.prompts import SYSTEM_PROMPT_GET
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.excel_utils import OfficeDocumentSource
from askui.utils.image_utils import (
    ImageSource,
    image_to_base64,
    scale_coordinates,
    scale_image_to_fit,
)
from askui.utils.pdf_utils import PdfSource
from askui.utils.source_utils import Source

from .utils import extract_click_coordinates


def build_system_prompt_locate(screen_width: str, screen_height: str) -> str:
    return f"Use a mouse and keyboard to interact with a computer, and take screenshots.\n* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.\n* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try taking another screenshot.\n* The screen's resolution is {screen_width}x{screen_height}.\n* The display number is 0\n* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.\n* If you tried clicking on a program or link but it failed to load, even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.\n* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.\n"  # noqa: E501


class _UnexpectedResponseError(Exception):
    """Exception raised when the response from Anthropic is unexpected."""

    def __init__(self, message: str, content: list[ContentBlockParam]) -> None:
        self.message = message
        self.content = content
        super().__init__(self.message)


class AnthropicModelSettings(BaseSettings):
    resolution: tuple[int, int] = Field(
        default_factory=lambda: (1280, 800),
        description="The resolution of images to use for the model",
        validation_alias="ANTHROPIC__RESOLUTION",
    )


class AnthropicModel(GetModel, LocateModel):
    def __init__(
        self,
        settings: AnthropicModelSettings,
        messages_api: MessagesApi,
        locator_serializer: VlmLocatorSerializer,
    ) -> None:
        self._settings = settings
        self._messages_api = messages_api
        self._locator_serializer = locator_serializer

    def _inference(
        self,
        image: ImageSource,
        prompt: str,
        system: str,
        model: str,
    ) -> str:
        scaled_image = scale_image_to_fit(
            image.root,
            self._settings.resolution,
        )
        message = self._messages_api.create_message(
            messages=[
                MessageParam(
                    role="user",
                    content=cast(
                        "list[ContentBlockParam]",
                        [
                            ImageBlockParam(
                                source=Base64ImageSourceParam(
                                    data=image_to_base64(scaled_image),
                                    media_type="image/png",
                                ),
                            ),
                            TextBlockParam(
                                text=prompt,
                            ),
                        ],
                    ),
                )
            ],
            model=model,
            system=system,
        )
        content: list[ContentBlockParam] = (
            message.content
            if isinstance(message.content, list)
            else [TextBlockParam(text=message.content)]
        )
        if len(content) != 1 or content[0].type != "text":
            error_msg = "Unexpected response from Anthropic API"
            raise _UnexpectedResponseError(error_msg, content)
        return content[0].text

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model: ModelComposition | str,
    ) -> PointList:
        if not isinstance(model, str):
            error_msg = "Model composition is not supported for Claude"
            raise NotImplementedError(error_msg)
        locator_serialized = (
            self._locator_serializer.serialize(locator)
            if isinstance(locator, Locator)
            else locator
        )
        try:
            prompt = f"Click on {locator_serialized}"
            screen_width = self._settings.resolution[0]
            screen_height = self._settings.resolution[1]
            content = self._inference(
                image=image,
                prompt=prompt,
                system=build_system_prompt_locate(
                    str(screen_width), str(screen_height)
                ),
                model=model,
            )
            return [
                scale_coordinates(
                    extract_click_coordinates(content),
                    image.root.size,
                    self._settings.resolution,
                    inverse=True,
                )
            ]
        except (
            _UnexpectedResponseError,
            ValueError,
            json.JSONDecodeError,
        ) as e:
            raise ElementNotFoundError(locator, locator_serialized) from e

    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        model: str,
    ) -> ResponseSchema | str:
        if isinstance(source, (PdfSource, OfficeDocumentSource)):
            err_msg = (
                f"PDF or Office Document processing is not supported for the model: "
                f"{model}"
            )
            raise NotImplementedError(err_msg)
        try:
            if response_schema is not None:
                error_msg = "Response schema is not yet supported for Anthropic"
                raise NotImplementedError(error_msg)
            return self._inference(
                image=source,
                prompt=query,
                system=SYSTEM_PROMPT_GET,
                model=model,
            )
        except _UnexpectedResponseError as e:
            if len(e.content) == 0:
                raise QueryNoResponseError(e.message, query) from e
            raise QueryUnexpectedResponseError(e.message, query, e.content) from e
