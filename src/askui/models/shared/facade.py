from typing import Callable, Type

from anthropic.types.beta import BetaMessageParam, BetaToolUseBlockParam
from typing_extensions import override

from askui.locators.locators import Locator
from askui.models.models import ActModel, GetModel, LocateModel, ModelComposition, Point
from askui.models.types.response_schemas import ResponseSchema
from askui.tools.anthropic.base import ToolResult
from askui.utils.image_utils import ImageSource


class ModelFacade(ActModel, GetModel, LocateModel):
    def __init__(
        self,
        act_model: ActModel,
        get_model: GetModel,
        locate_model: LocateModel,
    ) -> None:
        self._act_model = act_model
        self._get_model = get_model
        self._locate_model = locate_model

    @override
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
        self._act_model.act(
            messages=messages,
            model_choice=model_choice,
            on_message=on_message,
            on_tool_result=on_tool_result,
        )

    @override
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        return self._get_model.get(query, image, response_schema, model_choice)

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        return self._locate_model.locate(locator, image, model_choice)
