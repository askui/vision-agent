import json
import tempfile
from typing import Callable

import httpx
from gradio_client import Client, handle_file  # type: ignore
from PIL import Image
from typing_extensions import override

from askui.exceptions import AutomationError
from askui.locators.locators import Locator
from askui.locators.serializers import VlmLocatorSerializer
from askui.models.models import LocateModel, ModelComposition, ModelName, Point
from askui.utils.image_utils import ImageSource


class HFSpacesHandler(LocateModel):
    def __init__(self, locator_serializer: VlmLocatorSerializer) -> None:
        self._clients: dict[str, Client] = {}
        self._spaces: dict[
            str, Callable[[Image.Image, str, str | None], tuple[int, int]]
        ] = {
            ModelName.HF__SPACES__ASKUI__PTA_1: self.predict_askui_pta1,
            ModelName.HF__SPACES__OS_COPILOT__OS_ATLAS_BASE_7B: self.predict_os_atlas,
            ModelName.HF__SPACES__QWEN__QWEN2_VL_2B_INSTRUCT: self.predict_qwen2_vl,
            ModelName.HF__SPACES__QWEN__QWEN2_VL_7B_INSTRUCT: self.predict_qwen2_vl,
            ModelName.HF__SPACES__SHOWUI__2B: self.predict_showui,
        }
        self._locator_serializer = locator_serializer

    def get_spaces_names(self) -> list[str]:
        return list(self._spaces.keys())

    def get_space_client(self, space_name: str) -> Client:
        if space_name in list(self._clients.keys()):
            return self._clients[space_name]
        self._clients[space_name] = Client(space_name)
        return self._clients[space_name]

    @staticmethod
    def _rescale_bounding_boxes(
        bounding_boxes: list[list[float]],
        original_width: int,
        original_height: int,
        scaled_width: int = 1000,
        scaled_height: int = 1000,
    ) -> list[list[float]]:
        x_scale = original_width / scaled_width
        y_scale = original_height / scaled_height
        rescaled_boxes: list[list[float]] = []
        for box in bounding_boxes:
            xmin, ymin, xmax, ymax = box
            rescaled_box = [
                xmin * x_scale,
                ymin * y_scale,
                xmax * x_scale,
                ymax * y_scale,
            ]
            rescaled_boxes.append(rescaled_box)
        return rescaled_boxes

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        """Predict element location using Hugging Face Spaces."""
        if not isinstance(model_choice, str):
            error_msg = "Model composition is not supported for Hugging Face Spaces"
            raise NotImplementedError(error_msg)
        try:
            serialized_locator = (
                self._locator_serializer.serialize(locator)
                if isinstance(locator, Locator)
                else locator
            )
            return self._spaces[model_choice](
                image.root, serialized_locator, model_choice
            )
        except (ValueError, json.JSONDecodeError, httpx.HTTPError) as e:
            error_msg = f"Hugging Face Spaces Exception: {e}"
            raise AutomationError(error_msg) from e

    def predict_askui_pta1(
        self, screenshot: Image.Image, locator: str, model_name: str | None = None
    ) -> tuple[int, int]:
        client = self.get_space_client("AskUI/PTA-1")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            screenshot.save(temp_file, format="PNG")
            temp_file_path = temp_file.name
            result = client.predict(
                image=handle_file(temp_file_path),
                text_input=locator,
                model_id=model_name,
                api_name="/run_example",
            )
        target_box = json.loads(result[0])
        assert len(target_box) == 4, f"Malformed box: {target_box}"
        x1, y1, x2, y2 = target_box
        x = int((x1 + x2) / 2)
        y = int((y1 + y2) / 2)
        return x, y

    def predict_os_atlas(
        self, screenshot: Image.Image, locator: str, model_name: str | None = None
    ) -> tuple[int, int]:
        client = self.get_space_client("maxiw/OS-ATLAS")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            screenshot.save(temp_file, format="PNG")
            temp_file_path = temp_file.name
            result = client.predict(
                image=handle_file(temp_file_path),
                text_input=locator,
                model_id=model_name,
                api_name="/run_example",
            )
        target_box = json.loads(result[1])[0]
        assert len(target_box) == 4, f"Malformed box: {target_box}"
        x1, y1, x2, y2 = target_box
        x = int((x1 + x2) / 2)
        y = int((y1 + y2) / 2)
        return x, y

    def predict_qwen2_vl(
        self, screenshot: Image.Image, locator: str, model_name: str | None = None
    ) -> tuple[int, int]:
        client = self.get_space_client("maxiw/Qwen2-VL-Detection")
        system_prompt = "You are a helpfull assistant to detect objects in images. When asked to detect elements based on a description you return bounding boxes for all elements in the form of [xmin, ymin, xmax, ymax] whith the values beeing scaled to 1000 by 1000 pixels. When there are more than one result, answer with a list of bounding boxes in the form of [[xmin, ymin, xmax, ymax], [xmin, ymin, xmax, ymax], ...]."
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            screenshot.save(temp_file, format="PNG")
            temp_file_path = temp_file.name
            result = client.predict(
                image=handle_file(temp_file_path),
                text_input=locator,
                system_prompt=system_prompt,
                model_id=model_name,
                api_name="/run_example",
            )
        target_box = json.loads(result[1])
        target_box = self._rescale_bounding_boxes(
            target_box, screenshot.width, screenshot.height
        )[0]
        assert len(target_box) == 4, f"Malformed box: {target_box}"
        x1, y1, x2, y2 = target_box
        x = int((x1 + x2) / 2)
        y = int((y1 + y2) / 2)
        return x, y

    def predict_showui(
        self,
        screenshot: Image.Image,
        locator: str,
        model_name: str | None = None,  # noqa: ARG002
    ) -> tuple[int, int]:
        """Predict element location using ShowUI model."""
        client = self.get_space_client("showlab/ShowUI")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            screenshot.save(temp_file, format="PNG")
            temp_file_path = temp_file.name
            result = client.predict(
                image=handle_file(temp_file_path), query=locator, api_name="/on_submit"
            )
            output_value = json.loads(result[1])
            relative_x, relative_y = output_value
            x = int(relative_x * screenshot.width)
            y = int(relative_y * screenshot.height)
            return x, y
