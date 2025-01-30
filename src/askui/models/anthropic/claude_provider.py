import os
from anthropic import AnthropicBedrock, Anthropic
from enum import StrEnum
from ...logging import logger


class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    # VERTEX = "vertex"


PROVIDER_TO_DEFAULT_MODEL_NAME: dict[APIProvider, str] = {
    APIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    APIProvider.BEDROCK: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    # APIProvider.VERTEX: "claude-3-5-sonnet-v2@20241022",
}


class ClaudeApiProvider:
    api_provider: APIProvider
    api_client: AnthropicBedrock | Anthropic | None

    def __init__(self):
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        anthropic_bedrock_profile = os.getenv("ANTHROPIC_BEDROCK_PROFILE")

        self.api_provider = None
        self.api_client = None

        if anthropic_api_key:
            self.api_provider = APIProvider.ANTHROPIC
            self.api_client = Anthropic()
            logger.info("ANTHROPIC_API_KEY is set, using Anthropic API provider.")
        elif anthropic_bedrock_profile:
            self.api_provider = APIProvider.BEDROCK
            self.api_client = AnthropicBedrock(
                aws_profile=anthropic_bedrock_profile,
            )
            logger.info("ANTHROPIC_BEDROCK_PROFILE is set, using Anthropic Bedrock API provider.")
        else:
            raise ValueError("ANTHROPIC_API_KEY or ANTHROPIC_BEDROCK_PROFILE must be set")

        self.model = PROVIDER_TO_DEFAULT_MODEL_NAME[self.api_provider]

    def get_model_name(self):
        return self.model

    def get_api_client(self):
        return self.api_client

    def get_api_provider(self):
        return self.api_provider
