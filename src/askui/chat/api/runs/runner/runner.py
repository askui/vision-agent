import json
import logging
from abc import ABC, abstractmethod

from anthropic.types.beta import BetaCacheControlEphemeralParam, BetaTextBlockParam
from anyio.abc import ObjectStream
from asyncer import asyncify, syncify

from askui.chat.api.assistants.models import Assistant
from askui.chat.api.mcp_clients.manager import McpClientManagerManager
from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
from askui.chat.api.models import WorkspaceId
from askui.chat.api.runs.events.done_events import DoneEvent
from askui.chat.api.runs.events.error_events import (
    ErrorEvent,
    ErrorEventData,
    ErrorEventDataError,
)
from askui.chat.api.runs.events.events import Event
from askui.chat.api.runs.events.message_events import MessageEvent
from askui.chat.api.runs.events.run_events import RunEvent
from askui.chat.api.runs.events.service import RetrieveRunService
from askui.chat.api.runs.models import Run, RunError
from askui.custom_agent import CustomAgent
from askui.models.models import ModelName
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.models.shared.settings import ActSettings, MessageSettings
from askui.models.shared.tools import ToolCollection

logger = logging.getLogger(__name__)


class RunnerRunService(RetrieveRunService, ABC):
    @abstractmethod
    def save(self, run: Run, new: bool = False) -> None:
        raise NotImplementedError


class Runner:
    def __init__(
        self,
        workspace_id: WorkspaceId,
        assistant: Assistant,
        run: Run,
        chat_history_manager: ChatHistoryManager,
        mcp_client_manager_manager: McpClientManagerManager,
        run_service: RunnerRunService,
    ) -> None:
        self._workspace_id = workspace_id
        self._assistant = assistant
        self._run = run
        self._chat_history_manager = chat_history_manager
        self._mcp_client_manager_manager = mcp_client_manager_manager
        self._run_service = run_service

    def _retrieve(self) -> Run:
        return self._run_service.retrieve(
            thread_id=self._run.thread_id,
            run_id=self._run.id,
        )

    def _build_system(self) -> list[BetaTextBlockParam]:
        metadata = {
            "run_id": str(self._run.id),
            "thread_id": str(self._run.thread_id),
            "workspace_id": str(self._workspace_id),
            "assistant_id": str(self._run.assistant_id),
        }
        is_custom_assistant = self._assistant.workspace_id is not None
        custom_assistant_str = "custom " if is_custom_assistant else ""
        return [
            BetaTextBlockParam(
                type="text",
                text=f'You are an {custom_assistant_str}AI agent called "{self._assistant.name}" that is part of Caesr AI (AI agent platform developed by the company AskUI).',
            ),
            *(
                [
                    BetaTextBlockParam(
                        type="text",
                        text=self._assistant.system,
                    )
                ]
                if self._assistant.system
                else []
            ),
            BetaTextBlockParam(
                type="text",
                text="Metadata of current conversation: ",
            ),
            BetaTextBlockParam(
                type="text",
                text=json.dumps(metadata),
                cache_control=BetaCacheControlEphemeralParam(
                    type="ephemeral",
                ),
            ),
        ]

    async def _run_agent(
        self,
        send_stream: ObjectStream[Event],
    ) -> None:
        async def async_on_message(
            on_message_cb_param: OnMessageCbParam,
        ) -> MessageParam | None:
            created_message = await self._chat_history_manager.append_message(
                thread_id=self._run.thread_id,
                assistant_id=self._run.assistant_id,
                run_id=self._run.id,
                message=on_message_cb_param.message,
            )
            await send_stream.send(
                MessageEvent(
                    data=created_message,
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
            betas = tools.retrieve_tool_beta_flags()
            system = self._build_system()
            model = str(ModelName.CLAUDE__SONNET__4__20250514)
            messages = syncify(self._chat_history_manager.retrieve_message_params)(
                thread_id=self._run.thread_id,
                tools=tools.to_params(),
                system=system,
                model=model,
            )
            custom_agent = CustomAgent()
            custom_agent.act(
                messages,
                model=ModelName.ASKUI,
                on_message=on_message,
                tools=tools,
                settings=ActSettings(
                    messages=MessageSettings(
                        betas=betas,
                        model=model,
                        system=system,
                        thinking={"type": "enabled", "budget_tokens": 4096},
                        max_tokens=8192,
                    ),
                ),
            )

        await asyncify(_run_agent_inner)()

    async def run(
        self,
        send_stream: ObjectStream[Event],
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
