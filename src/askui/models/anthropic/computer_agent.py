from typing import TYPE_CHECKING, cast

from anthropic import Anthropic
from anthropic.types import (
    ThinkingConfigDisabledParam,
    ThinkingConfigEnabledParam,
    ThinkingConfigParam,
)
from typing_extensions import override

from askui.models.anthropic.settings import ClaudeComputerAgentSettings
from askui.models.models import ANTHROPIC_MODEL_NAME_MAPPING, ModelName
from askui.models.shared.computer_agent import ComputerAgent
from askui.models.shared.computer_agent_message_param import MessageParam
from askui.models.shared.tools import ToolCollection
from askui.reporting import Reporter

if TYPE_CHECKING:
    from anthropic.types.beta import BetaMessageParam


class ClaudeComputerAgent(ComputerAgent[ClaudeComputerAgentSettings]):
    def __init__(
        self,
        tool_collection: ToolCollection,
        reporter: Reporter,
        settings: ClaudeComputerAgentSettings,
    ) -> None:
        super().__init__(settings, tool_collection, reporter)
        self._client = Anthropic(
            api_key=self._settings.anthropic.api_key.get_secret_value()
        )

    @override
    def _create_message(
        self, messages: list[MessageParam], model_choice: str
    ) -> MessageParam:
        _thinking: ThinkingConfigParam = ThinkingConfigDisabledParam(type="disabled")

        if self._settings.thinking:
            _thinking = ThinkingConfigEnabledParam(
                type="enabled",
                budget_tokens=self._settings.thinking.budget_tokens,
            )

        response = self._client.beta.messages.with_raw_response.create(
            max_tokens=self._settings.max_tokens,
            messages=cast("list[BetaMessageParam]", messages),
            model=ANTHROPIC_MODEL_NAME_MAPPING[ModelName(model_choice)],
            system=[self._system],
            tools=self._tool_collection.to_params(),
            betas=self._settings.betas,
            thinking=_thinking,
            tool_choice=self._settings.tool_choice,
        )
        parsed_response = response.parse()
        return MessageParam.model_validate(parsed_response.model_dump())
