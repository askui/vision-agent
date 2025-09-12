import json
import logging
from abc import ABC, abstractmethod

from anyio.abc import ObjectStream
from asyncer import asyncify, syncify

from askui.chat.api.assistants.models import Assistant
from askui.chat.api.assistants.seeds import ANDROID_AGENT
from askui.chat.api.mcp_clients.manager import McpClientManagerManager
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
from askui.models.models import ModelName
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.models.shared.settings import ActSettings, MessageSettings
from askui.models.shared.tools import Tool, ToolCollection
from askui.utils.api_utils import LIST_LIMIT_MAX, ListQuery

logger = logging.getLogger(__name__)


def _get_android_tools() -> list[Tool]:
    from askui.tools.android.agent_os_facade import AndroidAgentOsFacade
    from askui.tools.android.ppadb_agent_os import PpadbAgentOs
    from askui.tools.android.tools import (
        AndroidDragAndDropTool,
        AndroidKeyCombinationTool,
        AndroidKeyTapEventTool,
        AndroidScreenshotTool,
        AndroidShellTool,
        AndroidSwipeTool,
        AndroidTapTool,
        AndroidTypeTool,
    )

    agent_os = PpadbAgentOs()
    act_agent_os_facade = AndroidAgentOsFacade(agent_os)
    return [
        AndroidScreenshotTool(act_agent_os_facade),
        AndroidTapTool(act_agent_os_facade),
        AndroidTypeTool(act_agent_os_facade),
        AndroidDragAndDropTool(act_agent_os_facade),
        AndroidKeyTapEventTool(act_agent_os_facade),
        AndroidSwipeTool(act_agent_os_facade),
        AndroidKeyCombinationTool(act_agent_os_facade),
        AndroidShellTool(act_agent_os_facade),
    ]


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
        mcp_client_manager_manager: McpClientManagerManager,
        run_service: RunnerRunService,
    ) -> None:
        self._workspace_id = workspace_id
        self._assistant = assistant
        self._run = run
        self._message_service = message_service
        self._message_translator = message_translator
        self._message_content_translator = message_translator.content_translator
        self._mcp_client_manager_manager = mcp_client_manager_manager
        self._run_service = run_service

    def _retrieve(self) -> Run:
        return self._run_service.retrieve(
            thread_id=self._run.thread_id,
            run_id=self._run.id,
        )

    def _build_system(self) -> str:
        base_system = self._assistant.system or ""
        metadata = {
            "run_id": str(self._run.id),
            "thread_id": str(self._run.thread_id),
            "workspace_id": str(self._workspace_id),
            "assistant_id": str(self._run.assistant_id),
        }
        return f"{base_system}\n\nMetadata of current conversation: {json.dumps(metadata)}".strip()

    async def _run_agent(
        self,
        send_stream: ObjectStream[Events],
    ) -> None:
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

        mcp_client = await self._mcp_client_manager_manager.get_mcp_client_manager(
            self._workspace_id
        )

        def _run_agent_inner() -> None:
            tools = ToolCollection(
                mcp_client=mcp_client,
                include=set(self._assistant.tools),
            )
            # Remove this after having extracted tools into Android MCP
            if self._run.assistant_id == ANDROID_AGENT.id:
                tools.append_tool(*_get_android_tools())
            betas = tools.retrieve_tool_beta_flags()
            custom_agent = CustomAgent()
            custom_agent.act(
                messages,
                model=ModelName.ASKUI,
                on_message=on_message,
                tools=tools,
                settings=ActSettings(
                    messages=MessageSettings(
                        betas=betas,
                        model=ModelName.CLAUDE__SONNET__4__20250514,
                        system=self._build_system(),
                        thinking={"type": "enabled", "budget_tokens": 2048},
                    ),
                ),
            )

        await asyncify(_run_agent_inner)()

    async def run(
        self,
        send_stream: ObjectStream[Events],
    ) -> None:
        try:
            self._mark_run_as_started()
            await send_stream.send(
                RunEvent(
                    data=self._run,
                    event="thread.run.in_progress",
                )
            )
            await self._run_agent(send_stream=send_stream)
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
