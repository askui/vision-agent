from typing import Any, Literal

from pydantic import BaseModel, Field

from askui.chat.api.messages.message_persisted_service import (
    MessageBase,
    MessagePersisted,
)
from askui.chat.api.models import FileId
from askui.models.shared.computer_agent_message_param import (
    ContentBlockParam,
    ImageBlockParam,
)


class MessageContentTextText(BaseModel):
    value: str
    annotations: list[Any] = Field(default_factory=list, max_length=0)


class MessageContentText(BaseModel):
    type: Literal["text"] = "text"
    text: MessageContentTextText

    @classmethod
    def from_str(cls, text: str) -> "MessageContentText":
        return cls(
            type="text",
            text=MessageContentTextText(value=text),
        )


class MessageContentImageUrlImageUrl(BaseModel):
    detail: Literal["auto", "low", "high"] = "auto"
    url: str


class MessageContentImageFileImageFile(BaseModel):
    file_id: FileId
    detail: Literal["auto", "low", "high"] = "auto"


class MessageContentImageFile(BaseModel):
    type: Literal["image_file"] = "image_file"
    image_file: MessageContentImageFileImageFile

    @classmethod
    def from_image_block_param(
        cls, image_block_param: ImageBlockParam
    ) -> "MessageContentImageFile":
        # TODO
        return cls(
            image_file=MessageContentImageFileImageFile(
                file_id="file_ge3tiojvg43tcmbqgu2tmkaypo2fnffeptznc7vdq",
            ),
        )


class MessageContentImageUrl(BaseModel):
    type: Literal["image_url"] = "image_url"
    image_url: MessageContentImageUrlImageUrl

    @classmethod
    def from_image_block_param(
        cls, image_block_param: ImageBlockParam
    ) -> "MessageContentImageUrl":
        match image_block_param.source.type:
            case "url":
                # TODO
                # url = image_block_param.source.url
                url = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Image_created_with_a_mobile_phone.png/500px-Image_created_with_a_mobile_phone.png"
            case "base64":
                # TODO
                # url = f"data:{image_block_param.source.media_type};base64,{image_block_param.source.data}"
                url = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Image_created_with_a_mobile_phone.png/500px-Image_created_with_a_mobile_phone.png"
        return cls(
            image_url=MessageContentImageUrlImageUrl(url=url),
        )


MessageContentBlock = (
    MessageContentText | MessageContentImageUrl | MessageContentImageFile
)

MessageContent = list[MessageContentBlock]


def map_message_param_content_to_message_content(
    content: str | list[ContentBlockParam],
) -> MessageContent:
    match content:
        case str():
            return [MessageContentText.from_str(content)]
        case list():
            result: MessageContent = []
            for block in content:
                match block.type:
                    case "image":
                        # TODO
                        result.append(
                            MessageContentImageFile.from_image_block_param(block)
                        )
                    case "text":
                        result.append(MessageContentText.from_str(block.text))
                    case "tool_use":
                        result.append(
                            MessageContentText.from_str(block.model_dump_json())
                        )
                    case "tool_result":
                        result.append(
                            MessageContentText.from_str(
                                f"Tool use id: {block.tool_use_id}\n"
                                f"Erroneous: {block.is_error}\n"
                                "Content:\n"
                            )
                        )
                        result.extend(
                            map_message_param_content_to_message_content(block.content)
                        )
            return result


class Message(MessageBase):
    content: MessageContent

    @classmethod
    def from_message_persisted(
        cls,
        message: MessagePersisted,
    ) -> "Message":
        return cls(
            **message.model_dump(exclude={"content"}),
            content=map_message_param_content_to_message_content(message.content),
        )
