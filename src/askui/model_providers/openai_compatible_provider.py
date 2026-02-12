"""OpenAICompatibleProvider — VLM access via any OpenAI-compatible endpoint."""

import json as json_lib
from typing import Any

from typing_extensions import override

from askui.model_providers.vlm_provider import VlmProvider
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
    ThinkingConfigParam,
    ToolChoiceParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.models.shared.prompts import SystemPrompt
from askui.models.shared.tools import ToolCollection


def _to_openai_messages(messages: list[MessageParam]) -> list[dict[str, Any]]:  # noqa: C901
    """Convert internal Anthropic-format messages to OpenAI chat format.

    Tool results (which are user-role blocks in Anthropic format) become
    separate ``role: "tool"`` messages in OpenAI format.

    Args:
        messages (list[MessageParam]): Internal message history.

    Returns:
        list[dict[str, Any]]: OpenAI-compatible message list.
    """
    result: list[dict[str, Any]] = []
    for msg in messages:
        if msg.role == "user":
            if isinstance(msg.content, str):
                result.append({"role": "user", "content": msg.content})
                continue
            user_parts: list[dict[str, Any]] = []
            for block in msg.content:
                if isinstance(block, ToolResultBlockParam):
                    if isinstance(block.content, str):
                        tool_content: str = block.content
                    else:
                        tool_content = " ".join(
                            b.text
                            for b in block.content
                            if isinstance(b, TextBlockParam)
                        )
                    result.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.tool_use_id,
                            "content": tool_content,
                        }
                    )
                elif isinstance(block, TextBlockParam):
                    user_parts.append({"type": "text", "text": block.text})
                elif isinstance(block, ImageBlockParam):
                    if isinstance(block.source, Base64ImageSourceParam):
                        media = block.source.media_type
                        url = f"data:{media};base64,{block.source.data}"
                    else:
                        url = block.source.url
                    user_parts.append({"type": "image_url", "image_url": {"url": url}})
            if user_parts:
                if len(user_parts) == 1 and user_parts[0]["type"] == "text":
                    result.append({"role": "user", "content": user_parts[0]["text"]})
                else:
                    result.append({"role": "user", "content": user_parts})
        elif msg.role == "assistant":
            if isinstance(msg.content, str):
                result.append({"role": "assistant", "content": msg.content})
                continue
            text_parts: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            for block in msg.content:
                if isinstance(block, TextBlockParam):
                    text_parts.append(block.text)
                elif isinstance(block, ToolUseBlockParam):
                    tool_calls.append(
                        {
                            "id": block.id,
                            "type": "function",
                            "function": {
                                "name": block.name,
                                "arguments": json_lib.dumps(block.input),
                            },
                        }
                    )
            msg_dict: dict[str, Any] = {"role": "assistant"}
            msg_dict["content"] = " ".join(text_parts) if text_parts else None
            if tool_calls:
                msg_dict["tool_calls"] = tool_calls
            result.append(msg_dict)
    return result


def _to_openai_tools(tools: ToolCollection) -> list[dict[str, Any]]:
    """Convert a ToolCollection to OpenAI function-calling format.

    Args:
        tools (ToolCollection): The tools to convert.

    Returns:
        list[dict[str, Any]]: OpenAI-compatible tools list.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": param["name"],
                "description": param.get("description", ""),
                "parameters": param.get("input_schema", {}),
            },
        }
        for param in tools.to_params()
    ]


def _from_openai_response(response: Any) -> MessageParam:
    """Convert an OpenAI chat completion response to a MessageParam.

    Args:
        response: OpenAI ChatCompletion response object.

    Returns:
        MessageParam: Internal message representation.
    """
    choice = response.choices[0]
    msg = choice.message
    from askui.models.shared.agent_message_param import ContentBlockParam

    content_blocks: list[ContentBlockParam] = []

    if msg.content:
        content_blocks.append(TextBlockParam(text=msg.content))

    if msg.tool_calls:
        content_blocks.extend(
            ToolUseBlockParam(
                id=tc.id,
                name=tc.function.name,
                input=json_lib.loads(tc.function.arguments),
            )
            for tc in msg.tool_calls
        )

    finish_reason = choice.finish_reason
    if finish_reason == "tool_calls":
        stop_reason = "tool_use"
    elif finish_reason == "length":
        stop_reason = "max_tokens"
    else:
        stop_reason = "end_turn"

    return MessageParam(
        role="assistant",
        content=content_blocks if content_blocks else "",
        stop_reason=stop_reason,
    )


class OpenAICompatibleProvider(VlmProvider):
    """VLM provider for any OpenAI-compatible chat completions endpoint.

    Converts the internal Anthropic-style message format to OpenAI's chat
    completions format, including tool-calling. Use this to connect to any
    model server that implements the OpenAI API (e.g. vLLM, Ollama, LM Studio,
    Azure OpenAI, or OpenRouter).

    Args:
        endpoint (str): Base URL of the OpenAI-compatible API
            (e.g. ``\"https://api.openai.com/v1\"``).
        api_key (str): API key for the endpoint.
        model_id (str): Model identifier sent as-is to the endpoint.

    Example:
        ```python
        from askui import AgentSettings, ComputerAgent
        from askui.model_providers import OpenAICompatibleProvider

        agent = ComputerAgent(settings=AgentSettings(
            vlm_provider=OpenAICompatibleProvider(
                endpoint=\"https://my-llm.example.com/v1\",
                api_key=\"sk-...\",
                model_id=\"my-model-v2\",
            )
        ))
        ```
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model_id: str,
    ) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._model_id_value = model_id

    @property
    @override
    def model_id(self) -> str:
        return self._model_id_value

    @property
    def _client(self):  # type: ignore[no-untyped-def]
        """Return a lazily-created OpenAI client."""
        if not hasattr(self, "_openai_client"):
            from openai import OpenAI

            self._openai_client = OpenAI(
                api_key=self._api_key,
                base_url=self._endpoint,
            )
        return self._openai_client

    @override
    def create_message(
        self,
        messages: list[MessageParam],
        tools: ToolCollection | None = None,
        max_tokens: int | None = None,
        betas: list[str] | None = None,
        system: SystemPrompt | None = None,
        thinking: ThinkingConfigParam | None = None,
        tool_choice: ToolChoiceParam | None = None,
        temperature: float | None = None,
    ) -> MessageParam:
        del betas, thinking  # not supported by OpenAI-compatible endpoints

        oai_messages: list[dict[str, Any]] = _to_openai_messages(messages)

        if system is not None:
            oai_messages = [
                {"role": "system", "content": str(system)},
                *oai_messages,
            ]

        kwargs: dict[str, Any] = {
            "model": self._model_id_value,
            "messages": oai_messages,
        }
        if tools is not None:
            oai_tools = _to_openai_tools(tools)
            if oai_tools:
                kwargs["tools"] = oai_tools
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        response = self._client.chat.completions.create(**kwargs)
        return _from_openai_response(response)
