import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Sequence

import anyio
from anyio.abc import ObjectStream
from asyncer import asyncify, syncify
from fastmcp import Client
from fastmcp.client.transports import MCPConfigTransport
from fastmcp.mcp_config import MCPConfig

from askui.agent import VisionAgent
from askui.android_agent import AndroidVisionAgent
from askui.chat.api.assistants.seeds import (
    ANDROID_VISION_AGENT,
    ASKUI_VISION_AGENT,
    ASKUI_WEB_AGENT,
    ASKUI_WEB_TESTING_AGENT,
    HUMAN_DEMONSTRATION_AGENT,
)
from askui.chat.api.mcp_configs.models import McpConfig
from askui.chat.api.mcp_configs.service import McpConfigService
from askui.chat.api.messages.service import MessageCreateRequest, MessageService
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
from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
)
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
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


def get_mcp_client(
    base_dir: Path,
) -> McpClient | None:
    """Get an MCP client from all available MCP configs.

    *Important*: This function can only handle up to 100 MCP server configs. Tool names
    are prefixed with the `McpConfigId` (used as the FastMCP MCP server name) to avoid
    conflicts.

    Args:
        base_dir: The base directory of the MCP configs.

    Returns:
        McpClient: A MCP client.
    """
    mcp_config_service = McpConfigService(base_dir)
    mcp_configs = mcp_config_service.find(ListQuery(limit=LIST_LIMIT_MAX, order="asc"))
    fast_mcp_config = build_fast_mcp_config(mcp_configs.data)
    return Client(fast_mcp_config) if fast_mcp_config.mcpServers else None


class Runner:
    def __init__(self, run: Run, base_dir: Path) -> None:
        self._run = run
        self._base_dir = base_dir
        self._runs_dir = base_dir / "runs"
        self._msg_service = MessageService(self._base_dir)
        self._agent_os = PynputAgentOs()

    async def _run_human_agent(self, send_stream: ObjectStream[Events]) -> None:
        message = self._msg_service.create(
            thread_id=self._run.thread_id,
            request=MessageCreateRequest(
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
            updated_run = self._retrieve_run()
            if self._should_abort(updated_run):
                break
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
                    message = self._msg_service.create(
                        thread_id=self._run.thread_id,
                        request=MessageCreateRequest(
                            role="user",
                            content=[
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
            screenshot = self._agent_os.screenshot()
            await anyio.sleep(0.1)
        self._agent_os.stop_listening()
        if len(recorded_events) == 0:
            text = "Nevermind, I didn't do anything."
            message = self._msg_service.create(
                thread_id=self._run.thread_id,
                request=MessageCreateRequest(
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
        agent_type: Literal["android", "vision", "web", "web_testing"],
        send_stream: ObjectStream[Events],
        mcp_client: McpClient | None,
    ) -> None:
        tools = ToolCollection(mcp_client=mcp_client)
        messages: list[MessageParam] = [
            MessageParam(
                role=msg.role,
                content=msg.content,
            )
            for msg in self._msg_service.find(
                thread_id=self._run.thread_id,
                query=ListQuery(limit=LIST_LIMIT_MAX),
            ).data
        ]

        async def async_on_message(
            on_message_cb_param: OnMessageCbParam,
        ) -> MessageParam | None:
            message = self._msg_service.create(
                thread_id=self._run.thread_id,
                request=MessageCreateRequest(
                    assistant_id=self._run.assistant_id
                    if on_message_cb_param.message.role == "assistant"
                    else None,
                    role=on_message_cb_param.message.role,
                    content=on_message_cb_param.message.content,
                    run_id=self._run.id,
                ),
            )
            await send_stream.send(
                MessageEvent(
                    data=message,
                    event="thread.message.created",
                )
            )
            updated_run = self._retrieve_run()
            if self._should_abort(updated_run):
                return None
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

            with VisionAgent() as agent:
                agent.act(
                    messages,
                    on_message=on_message,
                    tools=tools,
                )

        await asyncify(_run_agent_inner)()

    async def run(
        self,
        send_stream: ObjectStream[Events],
    ) -> None:
        mcp_client = get_mcp_client(self._base_dir)
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
            elif self._run.assistant_id == ASKUI_VISION_AGENT.id:
                await self._run_askui_vision_agent(
                    send_stream,
                    mcp_client,
                )
            elif self._run.assistant_id == ANDROID_VISION_AGENT.id:
                await self._run_askui_android_agent(
                    send_stream,
                    mcp_client,
                )
            elif self._run.assistant_id == ASKUI_WEB_AGENT.id:
                await self._run_askui_web_agent(
                    send_stream,
                    mcp_client,
                )
            elif self._run.assistant_id == ASKUI_WEB_TESTING_AGENT.id:
                await self._run_askui_web_testing_agent(
                    send_stream,
                    mcp_client,
                )
            updated_run = self._retrieve_run()
            if updated_run.status == "in_progress":
                updated_run.completed_at = datetime.now(tz=timezone.utc)
                self._update_run_file(updated_run)
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
                updated_run.cancelled_at = datetime.now(tz=timezone.utc)
                self._update_run_file(updated_run)
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
            updated_run = self._retrieve_run()
            updated_run.failed_at = datetime.now(tz=timezone.utc)
            updated_run.last_error = RunError(message=str(e), code="server_error")
            self._update_run_file(updated_run)
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
        self._run.started_at = datetime.now(tz=timezone.utc)
        self._update_run_file(self._run)

    def _should_abort(self, run: Run) -> bool:
        return run.status in ("cancelled", "cancelling", "expired")

    def _update_run_file(self, run: Run) -> None:
        run_file = self._runs_dir / f"{run.thread_id}__{run.id}.json"
        with run_file.open("w", encoding="utf-8") as f:
            f.write(run.model_dump_json())

    def _retrieve_run(self) -> Run:
        run_file = self._runs_dir / f"{self._run.thread_id}__{self._run.id}.json"
        with run_file.open("r", encoding="utf-8") as f:
            return Run.model_validate_json(f.read())
