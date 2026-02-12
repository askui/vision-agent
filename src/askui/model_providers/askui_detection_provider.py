"""AskUIDetectionProvider — UI element detection via AskUI's inference API."""

from functools import cached_property

from typing_extensions import override

from askui.locators.locators import Locator, Text
from askui.model_providers.detection_provider import DetectionProvider
from askui.models.models import DetectedElement
from askui.models.shared.settings import LocateSettings
from askui.models.types.geometry import PointList
from askui.utils.image_utils import ImageSource


class AskUIDetectionProvider(DetectionProvider):
    """Detection provider that routes requests to AskUI's inference API.

    Locates UI elements in screenshots using AskUI's hosted inference endpoint.
    Credentials are read from environment variables (`ASKUI_WORKSPACE_ID`,
    `ASKUI_TOKEN`) lazily — validation happens on the first API call, not at
    construction time.

    Args:
        workspace_id (str | None, optional): AskUI workspace ID. Reads
            `ASKUI_WORKSPACE_ID` from the environment if not provided.
        token (str | None, optional): AskUI API token. Reads `ASKUI_TOKEN`
            from the environment if not provided.

    Example:
        ```python
        from askui import AgentSettings, ComputerAgent
        from askui.model_providers import AskUIDetectionProvider

        agent = ComputerAgent(settings=AgentSettings(
            detection_provider=AskUIDetectionProvider(
                workspace_id="my-workspace",
                token="my-token",
            )
        ))
        ```
    """

    def __init__(
        self,
        workspace_id: str | None = None,
        token: str | None = None,
    ) -> None:
        self._workspace_id = workspace_id
        self._token = token

    @cached_property
    def _locate_api(self):  # type: ignore[no-untyped-def]
        """Lazily initialise the AskUiInferenceLocateApi on first use."""
        import os

        from askui.locators.serializers import AskUiLocatorSerializer
        from askui.models.askui.ai_element_utils import AiElementCollection
        from askui.models.askui.inference_api import AskUiInferenceApi
        from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings
        from askui.models.askui.locate_api import AskUiInferenceLocateApi
        from askui.reporting import NULL_REPORTER

        if self._workspace_id is not None:
            os.environ.setdefault("ASKUI_WORKSPACE_ID", self._workspace_id)
        if self._token is not None:
            os.environ.setdefault("ASKUI_TOKEN", self._token)

        settings = AskUiInferenceApiSettings()
        inference_api = AskUiInferenceApi(settings)
        locator_serializer = AskUiLocatorSerializer(
            ai_element_collection=AiElementCollection(),
            reporter=NULL_REPORTER,
        )
        return AskUiInferenceLocateApi(
            locator_serializer=locator_serializer,
            inference_api=inference_api,
        )

    @override
    def detect(
        self,
        locator: str | Locator,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> PointList:
        _locator: Locator = Text(locator) if isinstance(locator, str) else locator
        result: PointList = self._locate_api.locate(
            locator=_locator,
            image=image,
            locate_settings=locate_settings,
        )
        return result

    @override
    def detect_all(
        self,
        image: ImageSource,
        locate_settings: LocateSettings,
    ) -> list[DetectedElement]:
        result: list[DetectedElement] = self._locate_api.locate_all_elements(
            image=image,
            locate_settings=locate_settings,
        )
        return result
