"""LocateTool — tool that finds UI elements using a DetectionProvider."""

from typing_extensions import override

from askui.locators.locators import Locator
from askui.model_providers.detection_provider import DetectionProvider
from askui.models.models import DetectedElement
from askui.models.shared.settings import LocateSettings
from askui.models.shared.tool_tags import ToolTags
from askui.models.shared.tools import ToolCallResult, ToolWithAgentOS
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource


class LocateTool(ToolWithAgentOS):
    """Tool that locates UI elements on the screen.

    Used both as a tool available to the LLM in `act()` and as the direct
    implementation called by `agent.locate()` / `agent.locate_all()`. Backed
    by a `DetectionProvider`.

    Args:
        provider (DetectionProvider): The provider to use for element detection.
        locate_settings (LocateSettings | None, optional): Default settings for
            locate operations. Defaults to `LocateSettings()`.

    Example:
        ```python
        from askui.tools.locate_tool import LocateTool
        from askui.model_providers import AskUIDetectionProvider

        tool = LocateTool(provider=AskUIDetectionProvider())
        points = tool.run(locator=\"Submit button\", image=screenshot)
        ```
    """

    def __init__(
        self,
        provider: DetectionProvider,
        locate_settings: LocateSettings | None = None,
    ) -> None:
        super().__init__(
            required_tags=[ToolTags.SCALED_AGENT_OS.value],
            name="locate",
            description=(
                "Find the coordinates of a UI element on the screen."
                "Do only use this tool if your are explicitly told to do so!"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "locator": {
                        "type": "string",
                        "description": "Description of the UI element to locate.",
                    },
                },
                "required": ["locator"],
            },
        )
        self._provider = provider
        self._locate_settings = locate_settings or LocateSettings()

    @override
    def __call__(self, locator: str) -> ToolCallResult:
        """Call by the LLM tool-calling loop.

        Takes a screenshot and returns coordinates of the located element.

        Args:
            locator (str): Description of the element to find.
            **kwargs: Additional keyword arguments (ignored).

        Returns:
            ToolCallResult: The coordinates as a JSON string ``{"x": ..., "y": ...}``.
        """
        import json as json_lib

        screenshot = self.agent_os.screenshot()
        image = ImageSource(screenshot)
        points = self._provider.detect(
            locator=locator,
            image=image,
            locate_settings=self._locate_settings,
        )
        x, y = points[0]
        return json_lib.dumps({"x": x, "y": y})

    def run(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings | None = None,
    ) -> PointList:
        """Direct call used by `agent.locate()` / `agent.locate_all()`.

        Args:
            locator (str | Locator): Description or structured locator of the element.
            image (ImageSource): The screenshot to search in.
            locate_settings (LocateSettings | None, optional): Settings for this call.
                Overrides the tool's default settings if provided.

        Returns:
            PointList: List of (x, y) coordinate tuples.
        """
        _settings = locate_settings or self._locate_settings
        return self._provider.detect(
            locator=locator,
            image=image,
            locate_settings=_settings,
        )

    def run_all(
        self,
        image: ImageSource,
        locate_settings: LocateSettings | None = None,
    ) -> list[DetectedElement]:
        """Locate all detectable elements in the image.

        Direct call used by `agent.locate_all_elements()`.

        Args:
            image (ImageSource): The screenshot to analyze.
            locate_settings (LocateSettings | None, optional): Settings for this call.

        Returns:
            list[DetectedElement]: All detected elements.
        """
        _settings = locate_settings or self._locate_settings
        return self._provider.detect_all(
            image=image,
            locate_settings=_settings,
        )
