"""DetectionProvider interface for UI element detection."""

from abc import ABC, abstractmethod

from askui.locators.locators import Locator
from askui.models.models import DetectedElement
from askui.models.shared.settings import LocateSettings
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource


class DetectionProvider(ABC):
    """Interface for providers that locate UI elements in screenshots.

    A `DetectionProvider` accepts an image and a locator and returns the
    coordinates of matching UI elements. It is used for `agent.locate()`,
    `agent.click()`, and the `LocateTool`.

    Example:
        ```python
        from askui import AgentSettings, ComputerAgent
        from askui.model_providers import AskUIDetectionProvider

        provider = AskUIDetectionProvider(
            workspace_id="...",
            token="...",
        )
        agent = ComputerAgent(settings=AgentSettings(detection_provider=provider))
        ```
    """

    @abstractmethod
    def detect(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        """Find coordinates of a UI element in the given image.

        Args:
            locator (str | Locator): Description or structured locator of the element.
            image (ImageSource): The screenshot or image to search in.
            locate_settings (LocateSettings): Settings controlling detection behavior.

        Returns:
            PointList: List of (x, y) coordinate tuples for matching elements.

        Raises:
            ElementNotFoundError: If no matching elements are found.
        """

    def detect_all(
        self,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> list[DetectedElement]:
        """Locate all detectable elements in the given image.

        Args:
            image (ImageSource): The screenshot or image to analyze.
            locate_settings (LocateSettings): Settings controlling detection behavior.

        Returns:
            list[DetectedElement]: All detected elements with names, text, and bounds.
        """
        del image, locate_settings
        return []
