from typing_extensions import override

from askui.exceptions import AutomationError, ElementNotFoundError, ModelNotFoundError
from askui.locators.locators import AiElement, Locator, Prompt, Text
from askui.logger import logger
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.models import LocateModel, ModelComposition, ModelName, Point
from askui.utils.image_utils import ImageSource


class AskUiModelRouter(LocateModel):
    def __init__(self, inference_api: AskUiInferenceApi):
        self._inference_api = inference_api

    def _locate_with_askui_ocr(
        self, screenshot: ImageSource, locator: str | Text
    ) -> Point:
        locator = Text(locator) if isinstance(locator, str) else locator
        return self._inference_api.locate(
            locator, screenshot, model_choice=ModelName.ASKUI__OCR
        )

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        if (
            isinstance(model_choice, ModelComposition)
            or model_choice == ModelName.ASKUI
        ):
            logger.debug("Routing locate prediction to askui")
            locator = Text(locator) if isinstance(locator, str) else locator
            _model = model_choice if not isinstance(model_choice, str) else None
            return self._inference_api.locate(locator, image, _model or ModelName.ASKUI)
        if not isinstance(locator, str):
            error_msg = (
                f"Locators of type `{type(locator)}` are not supported for models "
                '"askui-pta", "askui-ocr" and "askui-combo" and "askui-ai-element". '
                "Please provide a `str`."
            )
            raise AutomationError(error_msg)
        if model_choice == ModelName.ASKUI__PTA:
            logger.debug("Routing locate prediction to askui-pta")
            return self._inference_api.locate(Prompt(locator), image, model_choice)
        if model_choice == ModelName.ASKUI__OCR:
            logger.debug("Routing locate prediction to askui-ocr")
            return self._locate_with_askui_ocr(image, locator)
        if model_choice == ModelName.ASKUI__COMBO:
            logger.debug("Routing locate prediction to askui-combo")
            prompt_locator = Prompt(locator)
            try:
                return self._inference_api.locate(prompt_locator, image, model_choice)
            except ElementNotFoundError:
                return self._locate_with_askui_ocr(image, locator)
        if model_choice == ModelName.ASKUI__AI_ELEMENT:
            logger.debug("Routing click prediction to askui-ai-element")
            _locator = AiElement(locator)
            return self._inference_api.locate(_locator, image, model_choice)
        raise ModelNotFoundError(model_choice, "locate")
