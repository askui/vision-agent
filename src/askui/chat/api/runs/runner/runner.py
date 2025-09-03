import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal, Sequence

import anthropic
import anyio
from anyio.abc import ObjectStream
from asyncer import asyncify, syncify
from fastmcp import Client
from fastmcp.client.transports import MCPConfigTransport
from fastmcp.mcp_config import MCPConfig

from askui.android_agent import AndroidVisionAgent
from askui.chat.api.assistants.models import Assistant
from askui.chat.api.assistants.seeds import (
    ANDROID_AGENT,
    HUMAN_DEMONSTRATION_AGENT,
    TESTING_AGENT,
    WEB_AGENT,
)
from askui.chat.api.mcp_configs.models import McpConfig
from askui.chat.api.mcp_configs.service import McpConfigService
from askui.chat.api.messages.models import MessageCreateParams
from askui.chat.api.messages.service import MessageService
from askui.chat.api.messages.translator import MessageTranslator
from askui.chat.api.models import RunId, ThreadId, WorkspaceId
from askui.chat.api.runs.models import Run, RunError
from askui.chat.api.runs.runner.events.done_events import DoneEvent
from askui.chat.api.runs.runner.events.error_events import (
    ErrorEvent,
    ErrorEventData,
    ErrorEventDataError,
)
from askui.chat.api.runs.runner.events.events import Events
from askui.chat.api.runs.runner.events.message_events import MessageEvent
from askui.chat.api.runs.runner.events.run_events import RunEvent
from askui.custom_agent import CustomAgent
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
)
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.models.shared.settings import ActSettings, MessageSettings
from askui.models.shared.tools import ToolCollection
from askui.tools.pynput_agent_os import PynputAgentOs
from askui.utils.api_utils import LIST_LIMIT_MAX, ListQuery
from askui.utils.image_utils import ImageSource
from askui.web_agent import WebVisionAgent
from askui.web_testing_agent import WebTestingAgent

if TYPE_CHECKING:
    from askui.tools.agent_os import InputEvent

logger = logging.getLogger(__name__)


def build_fast_mcp_config(mcp_configs: Sequence[McpConfig]) -> MCPConfig:
    mcp_config_dict = {
        mcp_config.id: mcp_config.mcp_server for mcp_config in mcp_configs
    }
    return MCPConfig(mcpServers=mcp_config_dict)


McpClient = Client[MCPConfigTransport]


class RunnerRunService(ABC):
    @abstractmethod
    def retrieve(self, thread_id: ThreadId, run_id: RunId) -> Run:
        raise NotImplementedError

    @abstractmethod
    def save(self, run: Run, new: bool = False) -> None:
        raise NotImplementedError


class Runner:
    def __init__(
        self,
        workspace_id: WorkspaceId,
        assistant: Assistant,
        run: Run,
        message_service: MessageService,
        message_translator: MessageTranslator,
        mcp_config_service: McpConfigService,
        run_service: RunnerRunService,
    ) -> None:
        self._workspace_id = workspace_id
        self._assistant = assistant
        self._run = run
        self._message_service = message_service
        self._message_translator = message_translator
        self._message_content_translator = message_translator.content_translator
        self._mcp_config_service = mcp_config_service
        self._run_service = run_service
        self._agent_os = PynputAgentOs()

    def _get_mcp_client(self) -> McpClient | None:
        mcp_configs = self._mcp_config_service.list_(
            workspace_id=self._workspace_id,
            query=ListQuery(limit=LIST_LIMIT_MAX, order="asc"),
        )
        fast_mcp_config = build_fast_mcp_config(mcp_configs.data)
        return Client(fast_mcp_config) if fast_mcp_config.mcpServers else None

    def _retrieve(self) -> Run:
        return self._run_service.retrieve(
            thread_id=self._run.thread_id,
            run_id=self._run.id,
        )

    async def _run_human_agent(self, send_stream: ObjectStream[Events]) -> None:
        message = self._message_service.create(
            thread_id=self._run.thread_id,
            params=MessageCreateParams(
                role="user",
                content=[
                    TextBlockParam(
                        type="text",
                        text="Let me take over and show you what I want you to do...",
                    ),
                ],
                run_id=self._run.id,
            ),
        )
        await send_stream.send(
            MessageEvent(
                data=message,
                event="thread.message.created",
            )
        )
        self._agent_os.start_listening()
        screenshot = self._agent_os.screenshot()
        await anyio.sleep(0.1)
        recorded_events: list[InputEvent] = []
        while True:
            updated_run = self._retrieve()
            if self._should_abort(updated_run):
                break
            updated_run.ping()
            self._run_service.save(updated_run)
            while event := self._agent_os.poll_event():
                if self._should_abort(updated_run):
                    break
                if not event.pressed:
                    recorded_events.append(event)
                    button = (
                        f'the "{event.button}" mouse button'
                        if event.button != "unknown"
                        else "a mouse button"
                    )
                    message = self._message_service.create(
                        thread_id=self._run.thread_id,
                        params=MessageCreateParams(
                            role="user",
                            content=await self._message_content_translator.from_anthropic(
                                [
                                    ImageBlockParam(
                                        type="image",
                                        source=Base64ImageSourceParam(
                                            data=ImageSource(screenshot).to_base64(),
                                            media_type="image/png",
                                        ),
                                    ),
                                    TextBlockParam(
                                        type="text",
                                        text=(
                                            f"I moved the mouse to x={event.x}, "
                                            f"y={event.y} and clicked {button}."
                                        ),
                                    ),
                                ]
                            ),
                            run_id=self._run.id,
                        ),
                    )
                    await send_stream.send(
                        MessageEvent(
                            data=message,
                            event="thread.message.created",
                        )
                    )
            screenshot = self._agent_os.screenshot()
            await anyio.sleep(0.1)
        self._agent_os.stop_listening()
        if len(recorded_events) == 0:
            text = "Nevermind, I didn't do anything."
            message = self._message_service.create(
                thread_id=self._run.thread_id,
                params=MessageCreateParams(
                    role="user",
                    content=[
                        TextBlockParam(
                            type="text",
                            text=text,
                        )
                    ],
                    run_id=self._run.id,
                ),
            )
            await send_stream.send(
                MessageEvent(
                    data=message,
                    event="thread.message.created",
                )
            )

    async def _run_askui_android_agent(
        self, send_stream: ObjectStream[Events], mcp_client: McpClient | None
    ) -> None:
        await self._run_agent(
            agent_type="android",
            send_stream=send_stream,
            mcp_client=mcp_client,
        )

    async def _run_askui_vision_agent(
        self, send_stream: ObjectStream[Events], mcp_client: McpClient | None
    ) -> None:
        await self._run_agent(
            agent_type="vision",
            send_stream=send_stream,
            mcp_client=mcp_client,
        )

    async def _run_askui_web_agent(
        self, send_stream: ObjectStream[Events], mcp_client: McpClient | None
    ) -> None:
        await self._run_agent(
            agent_type="web",
            send_stream=send_stream,
            mcp_client=mcp_client,
        )

    async def _run_askui_web_testing_agent(
        self, send_stream: ObjectStream[Events], mcp_client: McpClient | None
    ) -> None:
        await self._run_agent(
            agent_type="web_testing",
            send_stream=send_stream,
            mcp_client=mcp_client,
        )

    async def _run_agent(
        self,
        agent_type: Literal["android", "vision", "web", "web_testing", "custom"],
        send_stream: ObjectStream[Events],
        mcp_client: McpClient | None,
    ) -> None:
        tools = ToolCollection(
            mcp_client=mcp_client,
            include=set(self._assistant.tools) if self._assistant.tools else None,
        )
        messages: list[MessageParam] = [
            await self._message_translator.to_anthropic(msg)
            for msg in self._message_service.list_(
                thread_id=self._run.thread_id,
                query=ListQuery(limit=LIST_LIMIT_MAX, order="asc"),
            ).data
        ]

        async def async_on_message(
            on_message_cb_param: OnMessageCbParam,
        ) -> MessageParam | None:
            message = self._message_service.create(
                thread_id=self._run.thread_id,
                params=MessageCreateParams(
                    assistant_id=self._run.assistant_id
                    if on_message_cb_param.message.role == "assistant"
                    else None,
                    role=on_message_cb_param.message.role,
                    content=await self._message_content_translator.from_anthropic(
                        on_message_cb_param.message.content
                    ),
                    run_id=self._run.id,
                ),
            )
            await send_stream.send(
                MessageEvent(
                    data=message,
                    event="thread.message.created",
                )
            )
            updated_run = self._retrieve()
            if self._should_abort(updated_run):
                return None
            updated_run.ping()
            self._run_service.save(updated_run)
            return on_message_cb_param.message

        on_message = syncify(async_on_message)

        def _run_agent_inner() -> None:
            if agent_type == "android":
                with AndroidVisionAgent() as android_agent:
                    android_agent.act(
                        messages,
                        on_message=on_message,
                        tools=tools,
                    )
                return

            if agent_type == "web":
                with WebVisionAgent() as web_agent:
                    web_agent.act(
                        messages,
                        on_message=on_message,
                        tools=tools,
                    )
                return

            if agent_type == "web_testing":
                with WebTestingAgent() as web_testing_agent:
                    web_testing_agent.act(
                        messages,
                        on_message=on_message,
                        tools=tools,
                    )
                return

            _tools = ToolCollection(
                mcp_client=mcp_client,
                include=set(self._assistant.tools),
            )
            custom_agent = CustomAgent()
            custom_agent.act(
                messages,
                on_message=on_message,
                tools=_tools,
                settings=ActSettings(
                    messages=MessageSettings(
                        system=self._assistant.system or anthropic.NOT_GIVEN,
                        thinking={"type": "enabled", "budget_tokens": 2048},
                    ),
                ),
            )

        await asyncify(_run_agent_inner)()

    async def run(
        self,
        send_stream: ObjectStream[Events],
    ) -> None:
        mcp_client = self._get_mcp_client()
        self._mark_run_as_started()
        await send_stream.send(
            RunEvent(
                data=self._run,
                event="thread.run.in_progress",
            )
        )
        try:
            if self._run.assistant_id == HUMAN_DEMONSTRATION_AGENT.id:
                await self._run_human_agent(send_stream)
            elif self._run.assistant_id == ANDROID_AGENT.id:
                await self._run_askui_android_agent(
                    send_stream,
                    mcp_client,
                )
            elif self._run.assistant_id == WEB_AGENT.id:
                await self._run_askui_web_agent(
                    send_stream,
                    mcp_client,
                )
            elif self._run.assistant_id == TESTING_AGENT.id:
                await self._run_askui_web_testing_agent(
                    send_stream,
                    mcp_client,
                )
            else:
                await self._run_agent(
                    agent_type="custom",
                    send_stream=send_stream,
                    mcp_client=mcp_client,
                )
            updated_run = self._retrieve()
            if updated_run.status == "in_progress":
                updated_run.complete()
                self._run_service.save(updated_run)
                await send_stream.send(
                    RunEvent(
                        data=updated_run,
                        event="thread.run.completed",
                    )
                )
            if updated_run.status == "cancelling":
                await send_stream.send(
                    RunEvent(
                        data=updated_run,
                        event="thread.run.cancelling",
                    )
                )
                updated_run.cancel()
                self._run_service.save(updated_run)
                await send_stream.send(
                    RunEvent(
                        data=updated_run,
                        event="thread.run.cancelled",
                    )
                )
            if updated_run.status == "expired":
                await send_stream.send(
                    RunEvent(
                        data=updated_run,
                        event="thread.run.expired",
                    )
                )
            await send_stream.send(DoneEvent())
        except Exception as e:  # noqa: BLE001
            logger.exception("Exception in runner")
            updated_run = self._retrieve()
            updated_run.fail(RunError(message=str(e), code="server_error"))
            self._run_service.save(updated_run)
            await send_stream.send(
                RunEvent(
                    data=updated_run,
                    event="thread.run.failed",
                )
            )
            await send_stream.send(
                ErrorEvent(
                    data=ErrorEventData(error=ErrorEventDataError(message=str(e)))
                )
            )

    def _mark_run_as_started(self) -> None:
        self._run.start()
        self._run_service.save(self._run)

    def _should_abort(self, run: Run) -> bool:
        return run.status in ("cancelled", "cancelling", "expired")
