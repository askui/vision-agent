from pydantic import Field
from pydantic_settings import BaseSettings

from askui.models.shared.agent_message_param import ContentBlockParam


class UnexpectedResponseError(Exception):
    """Exception raised when the response from Anthropic is unexpected."""

    def __init__(self, message: str, content: list[ContentBlockParam]) -> None:
        self.message = message
        self.content = content
        super().__init__(self.message)


class AnthropicModelSettings(BaseSettings):
    resolution: tuple[int, int] = Field(
        default_factory=lambda: (1280, 800),
        description="The resolution of images to use for the model",
        validation_alias="ANTHROPIC__RESOLUTION",
    )
