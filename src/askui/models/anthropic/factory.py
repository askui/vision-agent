import functools
from typing import Literal

from anthropic import Anthropic, AnthropicBedrock, AnthropicVertex

from askui.models.askui.inference_api_settings import AskUiInferenceApiSettings

AnthropicApiProvider = Literal["anthropic", "askui", "bedrock", "vertex"]
AnthropicApiClient = Anthropic | AnthropicBedrock | AnthropicVertex


@functools.cache
def create_api_client(
    api_provider: AnthropicApiProvider,
) -> AnthropicApiClient:
    match api_provider:
        case "anthropic":
            return Anthropic()
        case "askui":
            settings = AskUiInferenceApiSettings()
            return Anthropic(
                api_key="DummyValueRequiredByAnthropicClient",
                base_url=f"{settings.base_url}/proxy/anthropic",
                default_headers={
                    "Authorization": settings.authorization_header,
                },
            )
        case "bedrock":
            return AnthropicBedrock()
        case "vertex":
            return AnthropicVertex()
