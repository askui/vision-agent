"""AskUIDetectionProvider — UI element detection via AskUI's inference API."""

from functools import cached_property

from pydantic import SecretStr
from typing_extensions import override

from askui.locators.locators import Locator, Text
from askui.locators.serializers import AskUiLocatorSerializer
from askui.model_providers.detection_provider import DetectionProvider
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.inference_api import AskUiInferenceApi
from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings
from askui.models.askui.locate_api import AskUiInferenceLocateApi
from askui.models.models import DetectedElement
from askui.models.shared.settings import LocateSettings
from askui.models.types.geometry import PointList
from askui.reporting import NULL_REPORTER
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
        locate_api (AskUiInferenceLocateApi | None, optional): Pre-configured
            locate API. If provided, `workspace_id` and `token` are ignored.

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
        locate_api: AskUiInferenceLocateApi | None = None,
    ) -> None:
        self._workspace_id = workspace_id
        self._token = token
        self._injected_locate_api = locate_api

    @cached_property
    def _locate_api(self) -> AskUiInferenceLocateApi:
        """Lazily initialise the AskUiInferenceLocateApi on first use."""
        if self._injected_locate_api is not None:
            return self._injected_locate_api

        settings_kwargs: dict[str, str | SecretStr] = {}
        if self._workspace_id is not None:
            settings_kwargs["workspace_id"] = self._workspace_id
        if self._token is not None:
            settings_kwargs["token"] = SecretStr(self._token)

        settings = AskUiInferenceApiSettings(**settings_kwargs)  # type: ignore[arg-type]
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
