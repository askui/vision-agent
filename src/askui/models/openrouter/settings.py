from pydantic import BaseModel, Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatCompletionsCreateSettings(BaseModel):
    """
    Settings for creating chat completions.

    Args:
        top_p (float | None, optional): An alternative to sampling with temperature,
            called nucleus sampling, where the model considers the results of the tokens
            with top_p probability mass. So `0.1` means only the tokens comprising
            the top 10% probability mass are considered. We generally recommend
            altering this or `temperature` but not both.
            Defaults to `None`.

        temperature (float, optional): What sampling temperature to use,
            between `0` and `2`. Higher values like `0.8` will make the output more
            random, while lower values like `0.2` will make it more focused and
            deterministic. We generally recommend altering this or `top_p` but not both.
            Defaults to `0.0`.

        max_tokens (int, optional): The maximum number of tokens that can be generated
            in the chat completion. This value can be used to control costs for text
            generated via API. This value is now deprecated in favor of
            `max_completion_tokens` for some models.
            Defaults to `1000`.

        seed (int | None, optional): If specified, the system will make a best effort
            to sample deterministically, such that repeated requests with the same seed
            and parameters should return the same result. Determinism is not guaranteed.
            Defaults to `None`.

        stop (str | list[str] | None, optional): Up to 4 sequences where the API
            will stop generating further tokens. The returned text will not contain the
            stop sequence.
            Defaults to `None`.

        frequency_penalty (float | None, optional): Number between `-2.0` and `2.0`.
            Positive values penalize new tokens based on their existing frequency
            in the text so far, decreasing the model's likelihood to repeat the same
            line verbatim.
            Defaults to `None`.

        presence_penalty (float | None, optional): Number between `-2.0` and `2.0`.
            Positive values penalize new tokens based on whether they appear in the text
            so far, increasing the model's likelihood to talk about new topics.
            Defaults to `None`.

    Returns:
        ChatCompletionsCreateSettings: The settings object for chat completions.

    Example:
        ```python
        settings = ChatCompletionsCreateSettings(top_p=0.9, temperature=0.7)
        ```
    """

    top_p: float | None = Field(
        default=None,
    )
    temperature: float = Field(
        default=0.0,
    )
    max_tokens: int = Field(
        default=1000,
    )
    seed: int | None = Field(
        default=None,
    )
    stop: str | list[str] | None = Field(
        default=None,
    )
    frequency_penalty: float | None = Field(
        default=None,
    )
    presence_penalty: float | None = Field(
        default=None,
    )


class OpenRouterSettings(BaseSettings):
    """
    Settings for OpenRouter API configuration.

    Args:
        model (str): OpenRouter model name. See https://openrouter.ai/models
        models (list[str]): OpenRouter model names
        base_url (HttpUrl): OpenRouter base URL. Defaults to https://openrouter.ai/api/v1
        chat_completions_create_settings (ChatCompletionsCreateSettings): Settings for ChatCompletions
    """  # noqa: E501

    model_config = SettingsConfigDict(env_prefix="OPEN_ROUTER_")
    model: str = Field(default="openrouter/auto", description="OpenRouter model name")
    models: list[str] = Field(
        default_factory=list, description="OpenRouter model names"
    )
    api_key: SecretStr = Field(
        default=...,
        description="API key for OpenRouter authentication",
    )
    base_url: HttpUrl = Field(
        default_factory=lambda: HttpUrl("https://openrouter.ai/api/v1"),
        description="OpenRouter base URL",
    )
    chat_completions_create_settings: ChatCompletionsCreateSettings = Field(
        default_factory=ChatCompletionsCreateSettings,
        description="Settings for ChatCompletions",
    )
