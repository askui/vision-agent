"""Provider for creating MessagesApi instances based on model names."""

import logging
from typing import TYPE_CHECKING

from askui.locators.serializers import VlmLocatorSerializer
from askui.models.anthropic.factory import AnthropicApiProvider, create_api_client
from askui.models.anthropic.messages_api import AnthropicMessagesApi

if TYPE_CHECKING:
    from askui.models.shared.messages_api import MessagesApi

logger = logging.getLogger(__name__)


class MessagesApiProvider:
    """Provider for creating MessagesApi instances based on model names.

    This class handles the logic of determining which API provider to use
    based on the model name prefix (anthropic/, askui/, bedrock/, vertex/).
    """

    def __init__(self) -> None:
        """Initialize the MessagesApiProvider."""
        self._locator_serializer = VlmLocatorSerializer()
        self._api_cache: dict[AnthropicApiProvider, AnthropicMessagesApi] = {}

    def _get_messages_api(
        self, api_provider: AnthropicApiProvider
    ) -> AnthropicMessagesApi:
        """Get or create a MessagesApi for the given provider.

        Args:
            api_provider: The API provider (anthropic, askui, bedrock, vertex)

        Returns:
            AnthropicMessagesApi instance
        """
        if api_provider not in self._api_cache:
            logger.debug("Creating new MessagesApi for provider '%s'", api_provider)
            self._api_cache[api_provider] = AnthropicMessagesApi(
                client=create_api_client(api_provider=api_provider),
                locator_serializer=self._locator_serializer,
            )
        return self._api_cache[api_provider]

    def get_messages_api_for_model(self, model_name: str) -> tuple["MessagesApi", str]:
        """Get the appropriate MessagesApi for a model name.

        This method parses the model name to determine the provider and
        returns the corresponding MessagesApi along with the actual model name.

        Args:
            model_name: Full model name, possibly with provider prefix
                (e.g., "anthropic/claude-...", "askui/claude-...", etc.)

        Returns:
            Tuple of (MessagesApi, actual_model_name)
                - MessagesApi: The appropriate API instance
                - actual_model_name: Model name without provider prefix

        Examples:
            >>> provider = MessagesApiProvider()
            >>> api, name = provider.get_messages_api_for_model("anthropic/claude-3")
            >>> # api is AnthropicMessagesApi with anthropic provider
            >>> # name is "claude-3"
            >>> api, name = provider.get_messages_api_for_model("askui/claude-3")
            >>> # api is AnthropicMessagesApi with askui provider
            >>> # name is "claude-3"
        """
        # Determine provider from model name prefix
        if model_name.startswith("anthropic/"):
            api_provider: AnthropicApiProvider = "anthropic"
            actual_model_name = model_name[len("anthropic/") :]
        elif model_name.startswith("askui/"):
            api_provider = "askui"
            actual_model_name = model_name[len("askui/") :]
        elif model_name.startswith("bedrock/"):
            api_provider = "bedrock"
            actual_model_name = model_name[len("bedrock/") :]
        elif model_name.startswith("vertex/"):
            api_provider = "vertex"
            actual_model_name = model_name[len("vertex/") :]
        else:
            # Default to askui provider for unprefixed models
            api_provider = "askui"
            actual_model_name = model_name
            logger.debug(
                "No provider prefix in model name '%s', using 'askui' as default",
                model_name,
            )

        messages_api = self._get_messages_api(api_provider)
        logger.debug(
            "Selected provider '%s' for model '%s'", api_provider, actual_model_name
        )

        return messages_api, actual_model_name
