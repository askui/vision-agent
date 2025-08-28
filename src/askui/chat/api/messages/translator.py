from PIL import Image

from askui.chat.api.files.service import FileService
from askui.chat.api.messages.models import (
    ContentBlockParam,
    FileImageSourceParam,
    ImageBlockParam,
    MessageParam,
    RequestDocumentBlockParam,
    ToolResultBlockParam,
)
from askui.data_extractor import DataExtractor
from askui.models.models import ModelName
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    TextBlockParam,
    UrlImageSourceParam,
)
from askui.models.shared.agent_message_param import (
    ContentBlockParam as AnthropicContentBlockParam,
)
from askui.models.shared.agent_message_param import (
    ImageBlockParam as AnthropicImageBlockParam,
)
from askui.models.shared.agent_message_param import (
    MessageParam as AnthropicMessageParam,
)
from askui.models.shared.agent_message_param import (
    ToolResultBlockParam as AnthropicToolResultBlockParam,
)
from askui.utils.excel_utils import OfficeDocumentSource
from askui.utils.image_utils import ImageSource, image_to_base64
from askui.utils.source_utils import Source, load_source


class RequestDocumentBlockParamTranslator:
    """Translator for RequestDocumentBlockParam to/from Anthropic format."""

    def __init__(self, file_service: FileService) -> None:
        self._file_service = file_service
        self._data_extractor = DataExtractor()

    def extract_content(
        self, source: Source, block: RequestDocumentBlockParam
    ) -> list[AnthropicContentBlockParam]:
        if isinstance(source, ImageSource):
            return [
                AnthropicImageBlockParam(
                    source=Base64ImageSourceParam(
                        data=source.to_base64(),
                        media_type="image/png",
                    ),
                    type="image",
                    cache_control=block.cache_control,
                )
            ]
        if isinstance(source, OfficeDocumentSource):
            with source.reader as r:
                data = r.read()
                return [
                    TextBlockParam(
                        text=data.decode(),
                        type="text",
                        cache_control=block.cache_control,
                    )
                ]
        text = self._data_extractor.get(
            query="""Extract all the content of the PDF to Markdown format.
            Preserve layout and formatting as much as possible, e.g., representing
            tables as HTML tables. For all images, videos, figures, extract text
            from it and describe what you are seeing, e.g., what is shown in the
            image or figure, and include that description.""",
            source=source,
            model=ModelName.ASKUI,
        )
        return [
            TextBlockParam(
                text=text,
                type="text",
                cache_control=block.cache_control,
            )
        ]

    async def to_anthropic(
        self, block: RequestDocumentBlockParam
    ) -> list[AnthropicContentBlockParam]:
        file, path = self._file_service.retrieve_file_content(block.source.file_id)
        source = load_source(path)
        content = self.extract_content(source, block)
        return [
            TextBlockParam(
                text=file.model_dump_json(),
                type="text",
                cache_control=block.cache_control,
            ),
        ] + content


class ImageBlockParamSourceTranslator:
    def __init__(self, file_service: FileService) -> None:
        self._file_service = file_service

    async def from_anthropic(
        self, source: UrlImageSourceParam | Base64ImageSourceParam
    ) -> UrlImageSourceParam | Base64ImageSourceParam | FileImageSourceParam:
        if source.type == "url":
            return source
        if source.type == "base64":  # noqa: RET503
            # Readd translation to FileImageSourceParam as soon as we support it in frontend
            return source
            # try:
            #     image = base64_to_image(source.data)
            #     bytes_io = BytesIO()
            #     image.save(bytes_io, format="PNG")
            #     bytes_io.seek(0)
            #     file = await self._file_service.upload_file(
            #         file=UploadFile(
            #             file=bytes_io,
            #             headers=Headers(
            #                 {
            #                     "Content-Type": "image/png",
            #                 }
            #             ),
            #         )
            #     )
            # except Exception as e:  # noqa: BLE001
            #     logger.warning(f"Failed to save image: {e}", exc_info=True)
            #     return source
            # else:
            #     return FileImageSourceParam(id=file.id, type="file")

    async def to_anthropic(
        self,
        source: UrlImageSourceParam | Base64ImageSourceParam | FileImageSourceParam,
    ) -> UrlImageSourceParam | Base64ImageSourceParam:
        if source.type == "url":
            return source
        if source.type == "base64":
            return source
        if source.type == "file":  # noqa: RET503
            file, path = self._file_service.retrieve_file_content(source.id)
            image = Image.open(path)
            return Base64ImageSourceParam(
                data=image_to_base64(image),
                media_type=file.media_type,
            )


class ImageBlockParamTranslator:
    def __init__(self, file_service: FileService) -> None:
        self.source_translator = ImageBlockParamSourceTranslator(file_service)

    async def from_anthropic(self, block: AnthropicImageBlockParam) -> ImageBlockParam:
        return ImageBlockParam(
            source=await self.source_translator.from_anthropic(block.source),
            type="image",
            cache_control=block.cache_control,
        )

    async def to_anthropic(self, block: ImageBlockParam) -> AnthropicImageBlockParam:
        return AnthropicImageBlockParam(
            source=await self.source_translator.to_anthropic(block.source),
            type="image",
            cache_control=block.cache_control,
        )


class ToolResultContentBlockParamTranslator:
    def __init__(self, file_service: FileService) -> None:
        self.image_translator = ImageBlockParamTranslator(file_service)

    async def from_anthropic(
        self, block: AnthropicImageBlockParam | TextBlockParam
    ) -> ImageBlockParam | TextBlockParam:
        if block.type == "image":
            return await self.image_translator.from_anthropic(block)
        return block

    async def to_anthropic(
        self, block: ImageBlockParam | TextBlockParam
    ) -> AnthropicImageBlockParam | TextBlockParam:
        if block.type == "image":
            return await self.image_translator.to_anthropic(block)
        return block


class ToolResultContentTranslator:
    def __init__(self, file_service: FileService) -> None:
        self.block_param_translator = ToolResultContentBlockParamTranslator(
            file_service
        )

    async def from_anthropic(
        self, content: str | list[AnthropicImageBlockParam | TextBlockParam]
    ) -> str | list[ImageBlockParam | TextBlockParam]:
        if isinstance(content, str):
            return content
        return [
            await self.block_param_translator.from_anthropic(block) for block in content
        ]

    async def to_anthropic(
        self, content: str | list[ImageBlockParam | TextBlockParam]
    ) -> str | list[AnthropicImageBlockParam | TextBlockParam]:
        if isinstance(content, str):
            return content
        return [
            await self.block_param_translator.to_anthropic(block) for block in content
        ]


class ToolResultBlockParamTranslator:
    def __init__(self, file_service: FileService) -> None:
        self.content_translator = ToolResultContentTranslator(file_service)

    async def from_anthropic(
        self, block: AnthropicToolResultBlockParam
    ) -> ToolResultBlockParam:
        return ToolResultBlockParam(
            tool_use_id=block.tool_use_id,
            type="tool_result",
            cache_control=block.cache_control,
            content=await self.content_translator.from_anthropic(block.content),
            is_error=block.is_error,
        )

    async def to_anthropic(
        self, block: ToolResultBlockParam
    ) -> AnthropicToolResultBlockParam:
        return AnthropicToolResultBlockParam(
            tool_use_id=block.tool_use_id,
            type="tool_result",
            cache_control=block.cache_control,
            content=await self.content_translator.to_anthropic(block.content),
            is_error=block.is_error,
        )


class MessageContentBlockParamTranslator:
    def __init__(self, file_service: FileService) -> None:
        self.image_translator = ImageBlockParamTranslator(file_service)
        self.tool_result_translator = ToolResultBlockParamTranslator(file_service)
        self.request_document_translator = RequestDocumentBlockParamTranslator(
            file_service
        )

    async def from_anthropic(
        self, block: AnthropicContentBlockParam
    ) -> list[ContentBlockParam]:
        if block.type == "image":
            return [await self.image_translator.from_anthropic(block)]
        if block.type == "tool_result":
            return [await self.tool_result_translator.from_anthropic(block)]
        return [block]

    async def to_anthropic(
        self, block: ContentBlockParam
    ) -> list[AnthropicContentBlockParam]:
        if block.type == "image":
            return [await self.image_translator.to_anthropic(block)]
        if block.type == "tool_result":
            return [await self.tool_result_translator.to_anthropic(block)]
        if block.type == "document":
            return await self.request_document_translator.to_anthropic(block)
        return [block]


class MessageContentTranslator:
    def __init__(self, file_service: FileService) -> None:
        self.block_param_translator = MessageContentBlockParamTranslator(file_service)

    async def from_anthropic(
        self, content: list[AnthropicContentBlockParam] | str
    ) -> list[ContentBlockParam] | str:
        if isinstance(content, str):
            return content
        lists_of_blocks = [
            await self.block_param_translator.from_anthropic(block) for block in content
        ]
        return [block for sublist in lists_of_blocks for block in sublist]

    async def to_anthropic(
        self, content: list[ContentBlockParam] | str
    ) -> list[AnthropicContentBlockParam] | str:
        if isinstance(content, str):
            return content
        lists_of_blocks = [
            await self.block_param_translator.to_anthropic(block) for block in content
        ]
        return [block for sublist in lists_of_blocks for block in sublist]


class MessageTranslator:
    def __init__(self, file_service: FileService) -> None:
        self.content_translator = MessageContentTranslator(file_service)

    async def from_anthropic(self, message: AnthropicMessageParam) -> MessageParam:
        return MessageParam(
            role=message.role,
            content=await self.content_translator.from_anthropic(message.content),
            stop_reason=message.stop_reason,
        )

    async def to_anthropic(self, message: MessageParam) -> AnthropicMessageParam:
        return AnthropicMessageParam(
            role=message.role,
            content=await self.content_translator.to_anthropic(message.content),
            stop_reason=message.stop_reason,
        )
