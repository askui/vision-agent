"""OpenAICompatibleActModel — ActModel implementation for OpenAI-compatible endpoint."""

from openai import OpenAI

from askui.models.openai.messages_api import OpenAICompatibleMessagesApi
from askui.models.shared.agent import AskUIAgent
from askui.models.shared.truncation_strategies import (
    SimpleTruncationStrategyFactory,
    TruncationStrategyFactory,
)
from askui.reporting import NULL_REPORTER, Reporter


class OpenAICompatibleActModel(AskUIAgent):
    """ActModel implementation for OpenAI-compatible endpoints.

    Extends AskUIAgent to use OpenAI-compatible APIs for tool-calling
    and message creation. Works with any OpenAI-compatible endpoint
    (e.g., vLLM, Ollama, LM Studio, Azure OpenAI, OpenRouter).

    Args:
        model_id (str): The model identifier to use.
        client (OpenAI): The OpenAI client for API calls.
        reporter (Reporter, optional): Reporter for logging. Defaults to NULL_REPORTER.
        truncation_strategy_factory (TruncationStrategyFactory | None, optional):
            Strategy for truncating message history. Defaults to
            SimpleTruncationStrategyFactory.
    """

    def __init__(
        self,
        model_id: str,
        client: OpenAI,
        reporter: Reporter = NULL_REPORTER,
        truncation_strategy_factory: TruncationStrategyFactory | None = None,
    ) -> None:
        messages_api = OpenAICompatibleMessagesApi(client=client)
        super().__init__(
            model_id=model_id,
            messages_api=messages_api,
            reporter=reporter,
            truncation_strategy_factory=(
                truncation_strategy_factory or SimpleTruncationStrategyFactory()
            ),
        )
