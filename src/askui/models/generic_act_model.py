"""Generic ActModel implementation for BYOM (Bring Your Own Model) use cases."""

from typing_extensions import override

from askui.models.models import ActModel
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb, OnMessageCbParam
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import ToolCollection


class GenericActModel(ActModel):
    """Generic implementation of ActModel that wraps a custom MessagesApi.

    This class allows users to bring their own model by providing a custom
    MessagesApi implementation. The GenericActModel handles the model_id
    and delegates message creation to the provided MessagesApi.

    Example:
        ```python
        from askui import VisionAgent
        from askui.models import GenericActModel, MessagesApi, MessageParam

        class MyMessagesApi(MessagesApi):
            def create_message(self, messages, model_id, tools, **kwargs):
                # Custom API integration for your LLM provider
                response = my_provider.chat(
                    messages=messages,
                    model=model_id,
                    tools=tools
                )
                return MessageParam.model_validate(response)

        # Create GenericActModel with custom MessagesApi
        my_act_model = GenericActModel(
            model_id="my-custom-llm-v2",
            messages_api=MyMessagesApi()
        )

        agent = VisionAgent(act_model=my_act_model)
        agent.act("Click the submit button")
        ```
    """

    def __init__(self, model_id: str, messages_api: MessagesApi) -> None:
        """Initialize GenericActModel.

        Args:
            model_id (str): The identifier of the LLM to use.
            messages_api (MessagesApi): Custom MessagesApi implementation.
        """
        self._model_id = model_id
        self._messages_api = messages_api

    @override
    def act(
        self,
        messages: list[MessageParam],
        act_settings: ActSettings,
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
    ) -> None:
        """Execute autonomous actions using the custom MessagesApi.

        Args:
            messages (list[MessageParam]): The message history.
            act_settings (ActSettings): The settings for this act operation.
            on_message (OnMessageCb | None, optional): Callback for new messages.
            tools (ToolCollection | None, optional): The tools for the agent.

        Returns:
            None
        """
        # Use the MessagesApi to create a message
        # The actual agent loop is handled by the Agent base implementation
        # This is a simplified version - real implementation would include
        # the full agentic loop with tool use

        response = self._messages_api.create_message(
            messages=messages,
            model_id=self._model_id,
            tools=tools,
            **act_settings.messages.model_dump(exclude_none=True),
        )

        if on_message:
            # Call callback with OnMessageCbParam
            on_message(OnMessageCbParam(message=response, messages=messages))
