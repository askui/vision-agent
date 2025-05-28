from typing import Type

from typing_extensions import override

from askui.locators.locators import Locator
from askui.models.askui.computer_agent import AskUiComputerAgent
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.askui.model_router import AskUiModelRouter
from askui.models.models import ActModel, GetModel, LocateModel, ModelComposition, Point
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import ImageSource


class AskUiFacade(ActModel, GetModel, LocateModel):
    def __init__(
        self,
        computer_agent: AskUiComputerAgent,
        inference_api: AskUiInferenceApi,
        model_router: AskUiModelRouter,
    ) -> None:
        self._computer_agent = computer_agent
        self._inference_api = inference_api
        self._model_router = model_router

    @override
    def act(self, goal: str, model_choice: str) -> None:
        self._computer_agent.act(goal, model_choice)

    @override
    def get(
        self,
        query: str,
        image: ImageSource,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        return self._inference_api.get(query, image, response_schema, model_choice)

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        return self._model_router.locate(locator, image, model_choice)
