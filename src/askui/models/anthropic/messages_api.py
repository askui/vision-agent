import json
from functools import cached_property
from typing import Type, cast

from anthropic import NOT_GIVEN, Anthropic, NotGiven
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import (
    BetaMessageParam,
    BetaTextBlockParam,
    BetaThinkingConfigParam,
    BetaToolChoiceParam,
)
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import override

from askui.locators.locators import Locator
from askui.locators.serializers import VlmLocatorSerializer
from askui.logger import logger
from askui.models.exceptions import (
    ElementNotFoundError,
    QueryNoResponseError,
    QueryUnexpectedResponseError,
)
from askui.models.models import (
    GetModel,
    LocateModel,
    ModelComposition,
    ModelName,
    Point,
)
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
)
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.prompts import SYSTEM_PROMPT_GET
from askui.models.shared.settings import MessageSettings
from askui.models.shared.tools import ToolCollection
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.dict_utils import IdentityDefaultDict
from askui.utils.image_utils import (
    ImageSource,
    image_to_base64,
    scale_coordinates_back,
    scale_image_with_padding,
)

from .utils import extract_click_coordinates


def build_system_prompt_locate(screen_width: str, screen_height: str) -> str:
    return f"Use a mouse and keyboard to interact with a computer, and take screenshots.\n* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.\n* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try taking another screenshot.\n* The screen's resolution is {screen_width}x{screen_height}.\n* The display number is 0\n* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.\n* If you tried clicking on a program or link but it failed to load, even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.\n* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.\n"  # noqa: E501


ANTHROPIC_MODEL_MAPPING: IdentityDefaultDict[ModelName | str, str] = (
    IdentityDefaultDict(
        {
            ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022: (
                "claude-3-5-sonnet-20241022"
            ),
            ModelName.CLAUDE__SONNET__4__20250514: "claude-sonnet-4-20250514",
            ModelName.ANTHROPIC__CLAUDE__3_5__SONNET__20241022.value: (
                "claude-3-5-sonnet-20241022"
            ),
            ModelName.CLAUDE__SONNET__4__20250514.value: "claude-sonnet-4-20250514",
        }
    )
)


class _UnexpectedResponseError(Exception):
    """Exception raised when the response from Anthropic is unexpected."""

    def __init__(self, message: str, content: list[ContentBlockParam]) -> None:
        self.message = message
        self.content = content
        super().__init__(self.message)


class AnthropicMessagesApiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_by_name=True,
        env_prefix="ANTHROPIC__",
        env_nested_delimiter="__",
    )

    api_key: SecretStr = Field(
        default=...,
        min_length=1,
        validation_alias="ANTHROPIC_API_KEY",
    )
    messages: MessageSettings = Field(default_factory=MessageSettings)
    resolution: tuple[int, int] = Field(
        default_factory=lambda: (1280, 800),
        description="The resolution of the screen to use for the model",
    )


class AnthropicMessagesApi(LocateModel, GetModel, MessagesApi):
    def __init__(
        self,
        locator_serializer: VlmLocatorSerializer,
        settings: AnthropicMessagesApiSettings | None = None,
    ) -> None:
        self._settings_default = settings
        self._locator_serializer = locator_serializer

    @cached_property
    def _settings(self) -> AnthropicMessagesApiSettings:
        if self._settings_default is None:
            return AnthropicMessagesApiSettings()
        return self._settings_default

    @cached_property
    def _client(self) -> Anthropic:
        return Anthropic(api_key=self._settings.api_key.get_secret_value())

    @override
    def create_message(
        self,
        messages: list[MessageParam],
        model: str,
        tools: ToolCollection | NotGiven = NOT_GIVEN,
        max_tokens: int | NotGiven = NOT_GIVEN,
        betas: list[AnthropicBetaParam] | NotGiven = NOT_GIVEN,
        system: str | list[BetaTextBlockParam] | NotGiven = NOT_GIVEN,
        thinking: BetaThinkingConfigParam | NotGiven = NOT_GIVEN,
        tool_choice: BetaToolChoiceParam | NotGiven = NOT_GIVEN,
    ) -> MessageParam:
        response = self._client.beta.messages.create(
            messages=[
                cast("BetaMessageParam", message.model_dump(exclude={"stop_reason"}))
                for message in messages
            ],
            tools=tools.to_params() if tools else NOT_GIVEN,
            max_tokens=max_tokens or self._settings.messages.max_tokens,
            model=ANTHROPIC_MODEL_MAPPING[model],
            betas=betas
            if not isinstance(betas, NotGiven)
            else self._settings.messages.betas,
            system=system or self._settings.messages.system,
            thinking=thinking or self._settings.messages.thinking,
            tool_choice=tool_choice or self._settings.messages.tool_choice,
            timeout=300.0,
        )
        return MessageParam.model_validate(response.model_dump())

    def _inference(
        self,
        image: ImageSource,
        prompt: str,
        system: str,
        model_choice: str,
    ) -> str:
        scaled_image = scale_image_with_padding(
            image.root,
            self._settings.resolution[0],
            self._settings.resolution[1],
        )
        message = self.create_message(
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
            model=model_choice,
            system=system,
        )
        content: list[ContentBlockParam] = (
            message.content
            if isinstance(message.content, list)
            else [TextBlockParam(text=message.content)]
        )
        if len(content) != 1 or content[0].type != "text":
            error_msg = f"Unexpected response from Anthropic: {content}"
            logger.error(error_msg)
            raise _UnexpectedResponseError(error_msg, content)
        return content[0].text

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
                model_choice=model_choice,
            )
            scaled_x, scaled_y = extract_click_coordinates(content)
            x, y = scale_coordinates_back(
                scaled_x,
                scaled_y,
                image.root.width,
                image.root.height,
                screen_width,
                screen_height,
            )
            return int(x), int(y)
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
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        try:
            if response_schema is not None:
                error_msg = "Response schema is not yet supported for Anthropic"
                raise NotImplementedError(error_msg)
            return self._inference(
                image=image,
                prompt=query,
                system=SYSTEM_PROMPT_GET,
                model_choice=model_choice,
            )
        except _UnexpectedResponseError as e:
            if len(e.content) == 0:
                raise QueryNoResponseError(e.message, query) from e
            raise QueryUnexpectedResponseError(e.message, query, e.content) from e
