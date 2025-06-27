from abc import ABC, abstractmethod

from askui.models.shared.agent_message_param import MessageParam


class MessagesApi(ABC):
    """Interface for creating messages using different APIs."""

    @abstractmethod
    def create_message(
        self, messages: list[MessageParam], model_choice: str
    ) -> MessageParam:
        """Create a message using the specific API implementation.

        Args:
            messages (list[MessageParam]): The message history.
            model_choice (str): The model to use for message creation.

        Returns:
            MessageParam: The created message.
        """
        raise NotImplementedError
