from typing import Callable, Literal

from pydantic import BaseModel

from askui.models.shared.computer_agent_message_param import MessageParam


class OnMessageCbParam(BaseModel):
    type: Literal["message"] = "message"
    message: MessageParam
    messages: list[MessageParam]


OnMessageCb = Callable[[OnMessageCbParam], MessageParam | None]
