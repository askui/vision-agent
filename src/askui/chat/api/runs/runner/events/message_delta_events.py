from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.messages.models import (
    MessageContent,
    MessageContentBlock,
    MessageContentImageFile,
    MessageContentImageUrl,
    MessageContentText,
)
from askui.chat.api.models import MessageId
from askui.chat.api.runs.runner.events.event_base import EventBase


class MessageDeltaContentText(MessageContentText):
    index: int = Field(ge=0)

    @classmethod
    def from_message_content(
        cls, message_content: MessageContentText, index: int
    ) -> "MessageDeltaContentText":
        return cls(
            index=index,
            text=message_content.text,
        )


class MessageDeltaContentImageFile(MessageContentImageFile):
    index: int = Field(ge=0)


class MessageDeltaContentImageUrl(MessageContentImageUrl):
    index: int = Field(ge=0)

    @classmethod
    def from_message_content(
        cls, message_content: MessageContentImageUrl, index: int
    ) -> "MessageDeltaContentImageUrl":
        return cls(
            index=index,
            image_url=message_content.image_url,
        )


MessageDeltaContentBlock = (
    MessageDeltaContentText | MessageDeltaContentImageUrl | MessageDeltaContentImageFile
)
MessageDeltaContent = list[MessageDeltaContentBlock]


def map_message_content_block_to_message_delta_content_block(
    block: MessageContentBlock,
    index: int = 0,
) -> MessageDeltaContentBlock:
    match block.type:
        case "image_file":
            return MessageDeltaContentImageFile(
                **block.model_dump(),
                index=index,
            )
        case "image_url":
            return MessageDeltaContentImageUrl(
                **block.model_dump(),
                index=index,
            )
        case "text":
            return MessageDeltaContentText(
                **block.model_dump(),
                index=index,
            )


def map_message_content_to_message_delta_content(
    message_content: MessageContent,
    start_index: int = 0,
) -> MessageDeltaContent:
    return [
        map_message_content_block_to_message_delta_content_block(
            block,
            index=start_index + i,
        )
        for i, block in enumerate(message_content)
    ]


class MessageDelta(BaseModel):
    content: MessageDeltaContent = Field(min_length=1)
    role: Literal["user", "assistant"]


class MessageDeltaEventData(BaseModel):
    id: MessageId
    delta: MessageDelta
    object: Literal["thread.message.delta"] = "thread.message.delta"


class MessageDeltaEvent(EventBase):
    data: MessageDeltaEventData
    event: Literal["thread.message.delta"] = "thread.message.delta"
