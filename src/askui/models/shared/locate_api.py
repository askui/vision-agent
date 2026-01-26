"""LocateApi interface and AskUI implementation for element location."""

import logging
from abc import ABC, abstractmethod

from askui.locators.locators import Locator
from askui.models.models import DetectedElement, LocateSettings
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)


class LocateApi(ABC):
    """Abstract base class for locate API implementations.

    This defines the interface for APIs that can locate UI elements in images.
    Different providers (AskUI, Anthropic, etc.) can implement this interface.
    """

    @abstractmethod
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        """Locate elements matching the locator in the image.

        Args:
            locator (str | Locator): Element locator (text or structured).
            image (ImageSource): Image to search in.
            locate_settings (LocateSettings): Settings for the locate operation.

        Returns:
            PointList: List of (x, y) coordinates for located elements.

        Raises:
            ElementNotFoundError: If no elements are found.
        """
        ...

    @abstractmethod
    def locate_all_elements(
        self,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> list[DetectedElement]:
        """Locate all elements in the image.

        Args:
            image (ImageSource): Image to analyze.
            locate_settings (LocateSettings): Settings for the locate operation.

        Returns:
            list[DetectedElement]: All detected elements.
        """
        ...
