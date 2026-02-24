"""GetTool — tool that answers questions about images using an ImageQAProvider."""

import json as json_lib
from typing import Any, Type

from typing_extensions import override

from askui.model_providers.image_qa_provider import ImageQAProvider
from askui.models.shared.settings import GetSettings
from askui.models.shared.tool_tags import ToolTags
from askui.models.shared.tools import ToolCallResult, ToolWithAgentOS
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import Source


class GetTool(ToolWithAgentOS):
    """Tool that extracts information from an image or document.

    Used both as a tool available to the LLM in `act()` and as the direct
    implementation called by `agent.get()`. Backed by an `ImageQAProvider`.

    Args:
        provider (ImageQAProvider): The provider to use for image Q&A.
        get_settings (GetSettings | None, optional): Default settings for
            get operations. Defaults to `GetSettings()`.

    Example:
        ```python
        from askui.tools.get_tool import GetTool
        from askui.model_providers import GoogleImageQAProvider

        tool = GetTool(provider=GoogleImageQAProvider())
        result = tool.run(query=\"What is the page title?\", image=screenshot)
        ```
    """

    def __init__(
        self,
        provider: ImageQAProvider,
        get_settings: GetSettings | None = None,
    ) -> None:
        super().__init__(
            required_tags=[ToolTags.SCALED_AGENT_OS.value],
            name="get",
            description=(
                "Extract information from the current screen or a provided image."
                "Do only use this tool if you are explicitly told to do so!"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What information to extract from the image.",
                    },
                },
                "required": ["query"],
            },
        )
        self._provider = provider
        self._get_settings = get_settings or GetSettings()

    @override
    def __call__(self, query: str) -> ToolCallResult:
        """Call by the LLM tool-calling loop.

        Takes a screenshot and answers the query against it.

        Args:
            query (str): What information to extract.
            **kwargs: Additional keyword arguments (ignored).

        Returns:
            ToolCallResult: The extracted information as a string.
        """
        screenshot = self.agent_os.screenshot()
        source: Source = ImageSource(screenshot)
        result = self._provider.query(
            query=query,
            source=source,
            response_schema=None,
            get_settings=self._get_settings,
        )
        return str(result)

    def run(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None = None,
        get_settings: GetSettings | None = None,
    ) -> ResponseSchema | str:
        """Direct call used by `agent.get()`.

        Args:
            query (str): What information to extract.
            source (Source): The image or document source to analyze.
            response_schema (Type[ResponseSchema] | None, optional): Optional
                Pydantic model defining the expected response structure.
            get_settings (GetSettings | None, optional): Settings for this call.
                Overrides the tool's default settings if provided.

        Returns:
            ResponseSchema | str: Extracted information.
        """
        _settings = get_settings or self._get_settings
        return self._provider.query(
            query=query,
            source=source,
            response_schema=response_schema,
            get_settings=_settings,
        )

    def to_json_schema(self) -> dict[str, Any]:
        """Return the JSON schema for telemetry / debugging."""
        result: dict[str, Any] = json_lib.loads(json_lib.dumps(self.input_schema))
        return result
