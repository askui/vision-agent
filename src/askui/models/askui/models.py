import json as json_lib
import logging
from typing import Any, Type

from google.genai.errors import ClientError
from typing_extensions import override

from askui.locators.locators import AiElement, Locator, Prompt, Text
from askui.locators.serializers import AskUiLocatorSerializer, AskUiSerializedLocator
from askui.models.askui.google_genai_api import AskUiGoogleGenAiApi
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.exceptions import (
    AutomationError,
    ElementNotFoundError,
    ModelNotFoundError,
    QueryNoResponseError,
    QueryUnexpectedResponseError,
)
from askui.models.models import (
    GetModel,
    LocateModel,
    ModelComposition,
    ModelName,
    PointList,
)
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.excel_utils import OfficeDocumentSource
from askui.utils.image_utils import ImageSource
from askui.utils.pdf_utils import PdfSource
from askui.utils.source_utils import Source

from ..types.response_schemas import to_response_schema

logger = logging.getLogger(__name__)


class AskUiLocateModel(LocateModel):
    def __init__(
        self,
        locator_serializer: AskUiLocatorSerializer,
        inference_api: AskUiInferenceApi,
    ) -> None:
        self._locator_serializer = locator_serializer
        self._inference_api = inference_api

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model: ModelComposition | str,
    ) -> PointList:
        if isinstance(model, ModelComposition) or model == ModelName.ASKUI:
            logger.debug("Routing locate prediction to askui")
            locator = Text(locator) if isinstance(locator, str) else locator
            _model = model if not isinstance(model, str) else None
            return self._locate(locator, image, _model or ModelName.ASKUI)
        if not isinstance(locator, str):
            error_msg = (
                f"Locators of type `{type(locator)}` are not supported for models "
                '"askui-pta", "askui-ocr" and "askui-combo" and "askui-ai-element". '
                "Please provide a `str`."
            )
            raise AutomationError(error_msg)
        if model == ModelName.ASKUI__PTA:
            logger.debug("Routing locate prediction to askui-pta")
            return self._locate(Prompt(locator), image, model)
        if model == ModelName.ASKUI__OCR:
            logger.debug("Routing locate prediction to askui-ocr")
            return self._locate_with_ocr(image, locator)
        if model == ModelName.ASKUI__COMBO:
            logger.debug("Routing locate prediction to askui-combo")
            prompt_locator = Prompt(locator)
            try:
                return self._locate(prompt_locator, image, model)
            except ElementNotFoundError:
                return self._locate_with_ocr(image, locator)
        if model == ModelName.ASKUI__AI_ELEMENT:
            logger.debug("Routing click prediction to askui-ai-element")
            _locator = AiElement(locator)
            return self._locate(_locator, image, model)
        raise ModelNotFoundError(model, "locate")

    def _locate_with_ocr(
        self, screenshot: ImageSource, locator: str | Text
    ) -> PointList:
        locator = Text(locator) if isinstance(locator, str) else locator
        return self._locate(locator, screenshot, model=ModelName.ASKUI__OCR)

    def _locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model: ModelComposition | str,
    ) -> PointList:
        serialized_locator = (
            self._locator_serializer.serialize(locator=locator)
            if isinstance(locator, Locator)
            else AskUiSerializedLocator(customElements=[], instruction=locator)
        )
        logger.debug(
            "Locator serialized",
            extra={"serialized_locator": json_lib.dumps(serialized_locator)},
        )
        json: dict[str, Any] = {
            "image": image.to_data_url(),
            "instruction": f"get element {serialized_locator['instruction']}",
        }
        if "customElements" in serialized_locator:
            json["customElements"] = serialized_locator["customElements"]
        if isinstance(model, ModelComposition):
            json["modelComposition"] = model.model_dump(by_alias=True)
            logger.debug(
                "Model composition",
                extra={"modelComposition": json_lib.dumps(json["modelComposition"])},
            )
        response = self._inference_api.post(path="/inference", json=json)
        content = response.json()
        assert content["type"] == "DETECTED_ELEMENTS", (
            f"Received unknown content type {content['type']}"
        )
        detected_elements = content["data"]["detected_elements"]
        if len(detected_elements) == 0:
            raise ElementNotFoundError(locator, serialized_locator)

        return [
            (
                int((element["bndbox"]["xmax"] + element["bndbox"]["xmin"]) / 2),
                int((element["bndbox"]["ymax"] + element["bndbox"]["ymin"]) / 2),
            )
            for element in detected_elements
        ]


class AskUiGetModel(GetModel):
    """A GetModel implementation that is supposed to be as comprehensive and
    powerful as possible using the available AskUi models.

    This model first attempts to use the Google GenAI API for information extraction.
    If the Google GenAI API fails (e.g., no response, unexpected response, or other
    errors), it falls back to using the AskUI Inference API.
    """

    def __init__(
        self,
        google_genai_api: AskUiGoogleGenAiApi,
        inference_api: AskUiInferenceApi,
    ) -> None:
        self._google_genai_api = google_genai_api
        self._inference_api = inference_api

    def _get_vqa(
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
        json: dict[str, Any] = {
            "image": source.to_data_url(),
            "prompt": query,
        }
        _response_schema = to_response_schema(response_schema)
        json_schema = _response_schema.model_json_schema()
        json["config"] = {"json_schema": json_schema}
        logger.debug(
            "Json schema used for response",
            extra={"json_schema": json_lib.dumps(json["config"]["json_schema"])},
        )
        response = self._inference_api.post(path="/vqa/inference", json=json)
        content = response.json()
        data = content["data"]["response"]
        validated_response = _response_schema.model_validate(data)
        return validated_response.root

    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        model: str,
    ) -> ResponseSchema | str:
        try:
            logger.debug("Attempting to use Google GenAI API")
            return self._google_genai_api.get(
                query=query,
                source=source,
                response_schema=response_schema,
                model=model,
            )
        except (
            ClientError,
            QueryNoResponseError,
            QueryUnexpectedResponseError,
            NotImplementedError,
        ) as e:
            if isinstance(e, ClientError) and e.code != 400:
                raise
            logger.debug(
                (
                    "Google GenAI API failed with exception that may not occur with "
                    "other models/apis. Falling back to Inference API..."
                ),
                extra={"error": str(e)},
            )
            return self._get_vqa(
                query=query,
                source=source,
                response_schema=response_schema,
                model=model,
            )
