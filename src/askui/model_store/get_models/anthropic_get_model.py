from typing import Type

from typing_extensions import override

from askui.models.anthropic.messages_api import built_messages_for_get_and_locate
from askui.models.anthropic.settings import (
    AnthropicModelSettings,
    UnexpectedResponseError,
)
from askui.models.exceptions import (
    QueryNoResponseError,
    QueryUnexpectedResponseError,
)
from askui.models.models import GetModel
from askui.models.shared.agent_message_param import (
    ContentBlockParam,
    TextBlockParam,
)
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.settings import GetSettings
from askui.models.types.response_schemas import ResponseSchema
from askui.prompts.get_prompts import SYSTEM_PROMPT_GET
from askui.utils.excel_utils import OfficeDocumentSource
from askui.utils.image_utils import scale_image_to_fit
from askui.utils.pdf_utils import PdfSource
from askui.utils.source_utils import Source


class AnthropicGetModel(GetModel):
    def __init__(
        self, model_id: str, settings: AnthropicModelSettings, messages_api: MessagesApi
    ) -> None:
        self._model_id = model_id
        self._settings = settings
        self._messages_api = messages_api

    def _validate_content(self, content: list[ContentBlockParam]) -> TextBlockParam:
        """Validate that content is a single text block.

        Args:
            content (list[ContentBlockParam]): The content to validate

        Raises:
            UnexpectedResponseError: If content is not a single text block
        """
        if len(content) != 1 or content[0].type != "text":
            error_msg = "Unexpected response from Anthropic API"
            raise UnexpectedResponseError(error_msg, content)
        return content[0]

    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        get_settings: GetSettings,
    ) -> ResponseSchema | str:
        if isinstance(source, (PdfSource, OfficeDocumentSource)):
            err_msg = (
                f"PDF or Office Document processing is not supported for the model: "
                f"{self._model_id}"
            )
            raise NotImplementedError(err_msg)
        try:
            if response_schema is not None:
                error_msg = "Response schema is not yet supported for Anthropic"
                raise NotImplementedError(error_msg)
            scaled_image = scale_image_to_fit(
                source.root,
                self._settings.resolution,
            )
            messages = built_messages_for_get_and_locate(scaled_image, query)
            message = self._messages_api.create_message(
                messages=messages,
                model_id=self._model_id,
                system=SYSTEM_PROMPT_GET,
            )
            content: list[ContentBlockParam] = (
                message.content
                if isinstance(message.content, list)
                else [TextBlockParam(text=message.content)]
            )
            content_text = self._validate_content(content)
        except UnexpectedResponseError as e:
            if len(e.content) == 0:
                raise QueryNoResponseError(e.message, query) from e
            raise QueryUnexpectedResponseError(e.message, query, e.content) from e
        else:
            return content_text.text
