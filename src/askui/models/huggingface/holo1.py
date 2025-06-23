"""Holo-1 Vision Language Model implementation for element location.

This module provides the Holo1LocateModel class that uses the Holo-1 VLM
for locating UI elements on screen based on natural language descriptions.
"""

import json

from typing_extensions import override

from askui.exceptions import AutomationError, ElementNotFoundError
from askui.locators.locators import Locator
from askui.locators.serializers import VlmLocatorSerializer
from askui.logger import logger
from askui.models.models import LocateModel, ModelComposition, Point
from askui.utils.image_utils import ImageSource


class Holo1LocateModel(LocateModel):
    """Holo-1 model implementation for locating UI elements.

    This model uses the Holo-1 Vision Language Model for element detection
    and supports both GPU and CPU inference.

    Attributes:
        _model_name: The Hugging Face model identifier
        _device: The device to run inference on (cuda/cpu)
        _locator_serializer: Serializer for converting locators to prompts
    """

    def __init__(
        self,
        locator_serializer: VlmLocatorSerializer,
        model_name: str = "Hcompany/Holo1-7B",
        device: str | None = None,
    ) -> None:
        """Initialize the Holo-1 model.

        Args:
            locator_serializer: Serializer for converting locators to prompts
            model_name: The Hugging Face model identifier
            device: Device to run inference on. If None, auto-detects GPU availability
        """
        self._model_name = model_name
        self._locator_serializer = locator_serializer
        self._model = None
        self._processor = None

        # Lazy import to avoid loading heavy dependencies
        import torch

        if device is None:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self._device = device

        logger.info(f"Holo-1 model will use device: {self._device}")

    def _load_model(self) -> None:
        """Lazy load the model and processor."""
        if self._model is not None:
            return

        logger.info(f"Loading Holo-1 model from {self._model_name}")

        try:
            from transformers import AutoModelForImageTextToText, AutoProcessor

            self._processor = AutoProcessor.from_pretrained(self._model_name)
            self._model = AutoModelForImageTextToText.from_pretrained(
                self._model_name,
                torch_dtype="auto",
                device_map=self._device if self._device != "cpu" else None,
            )

            # Set to evaluation mode
            self._model.eval()

            logger.info("Holo-1 model loaded successfully")

        except Exception as e:
            error_msg = f"Failed to load Holo-1 model: {e}"
            logger.error(error_msg)
            raise AutomationError(error_msg) from e

    def _parse_model_output(
        self, output: str, _image_width: int, _image_height: int
    ) -> Point:
        """Parse the model output to extract coordinates.

        Args:
            output: The model's text output
            image_width: Width of the input image
            image_height: Height of the input image

        Returns:
            A tuple of (x, y) coordinates

        Raises:
            ElementNotFoundError: If coordinates cannot be parsed from output
        """
        try:
            # Expected format: {"bbox": [x1, y1, x2, y2]} or similar
            # This may need adjustment based on actual model output format
            if "bbox" in output:
                bbox_data = json.loads(output)
                bbox = bbox_data["bbox"]
                x1, y1, x2, y2 = bbox

                # Return center point
                x = int((x1 + x2) / 2)
                y = int((y1 + y2) / 2)

                return x, y

            # Try to extract coordinates from text
            # Format might be "Element at (x, y)" or similar
            import re

            coord_pattern = r"\\((\\d+),\\s*(\\d+)\\)"
            match = re.search(coord_pattern, output)

            if match:
                x = int(match.group(1))
                y = int(match.group(2))
                return x, y

            error_msg = f"Could not parse coordinates from model output: {output}"
            raise ValueError(error_msg)  # noqa: TRY301

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            error_msg = f"Failed to parse Holo-1 output: {output}"
            logger.error(error_msg)
            empty_locator = ""
            raise ElementNotFoundError(empty_locator, empty_locator) from e

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> Point:
        """Locate an element using the Holo-1 model.

        Args:
            locator: Element description or locator object
            image: Screenshot to analyze
            model_choice: Model selection (ignored for single model)

        Returns:
            Coordinates of the located element as (x, y) tuple

        Raises:
            AutomationError: If model inference fails
            ElementNotFoundError: If element cannot be found
        """
        if isinstance(model_choice, ModelComposition):
            error_msg = "Model composition is not supported for Holo-1"
            raise NotImplementedError(error_msg)

        # Ensure model is loaded
        self._load_model()

        # Serialize locator if needed
        serialized_locator = (
            self._locator_serializer.serialize(locator)
            if isinstance(locator, Locator)
            else locator
        )

        # Prepare messages for chat template
        messages = [
            {"role": "user", "content": f"Locate the UI element: {serialized_locator}"}
        ]

        try:
            # Apply chat template and process
            text = self._processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            inputs = self._processor(
                text=[text], images=image.root, return_tensors="pt"
            )

            # Move to device if not CPU
            if self._device != "cpu":
                inputs = inputs.to(self._device)

            # Generate response
            import torch

            with torch.no_grad():
                generated_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=128,
                )

            # Trim generated tokens and decode
            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(
                    inputs.input_ids, generated_ids, strict=False
                )
            ]

            response = self._processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True
            )[0]

            logger.debug(f"Holo-1 response: {response}")

            # Parse coordinates from response
            return self._parse_model_output(
                response, image.root.width, image.root.height
            )

        except Exception as e:
            if isinstance(e, (ElementNotFoundError, NotImplementedError)):
                raise
            error_msg = f"Holo-1 inference failed: {e}"
            logger.error(error_msg)
            raise AutomationError(error_msg) from e
