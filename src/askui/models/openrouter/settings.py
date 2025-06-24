from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings

from askui.models.shared.settings import ChatCompletionsCreateSettings


class OpenRouterSettings(BaseSettings):
    """
    Settings for OpenRouter API configuration.

    Args:
        model (str): OpenRouter model name. See https://openrouter.ai/models
        models (list[str]): OpenRouter model names
        base_url (HttpUrl): OpenRouter base URL. Defaults to https://openrouter.ai/api/v1
        chat_completions_create_settings (ChatCompletionsCreateSettings): Settings for ChatCompletions
    """  # noqa: E501

    model: str = Field(default="openrouter/auto", description="OpenRouter model name")
    models: list[str] = Field(
        default_factory=list, description="OpenRouter model names"
    )
    open_router_api_key: SecretStr = Field(
        default=...,
        description="API key for OpenRouter authentication",
        validation_alias="OPEN_ROUTER_API_KEY",
    )
    base_url: HttpUrl = Field(
        default_factory=lambda: HttpUrl("https://openrouter.ai/api/v1"),
        description="OpenRouter base URL",
    )
    chat_completions_create_settings: ChatCompletionsCreateSettings = Field(
        default_factory=ChatCompletionsCreateSettings,
        description="Settings for ChatCompletions",
    )
