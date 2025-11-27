import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from anthropic.types.beta import BetaCacheControlEphemeralParam, BetaTextBlockParam
from anyio.abc import ObjectStream
from asyncer import asyncify, syncify

from askui.chat.api.assistants.models import Assistant
from askui.chat.api.mcp_clients.manager import McpClientManagerManager
from askui.chat.api.messages.chat_history_manager import ChatHistoryManager
from askui.chat.api.models import MessageId, RunId, ThreadId, WorkspaceId
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
from askui.chat.api.runs.models import (
    Run,
    RunCancel,
    RunComplete,
    RunError,
    RunFail,
    RunModify,
    RunPing,
    RunStart,
)
from askui.chat.api.settings import Settings
from askui.custom_agent import CustomAgent
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCbParam
from askui.models.shared.settings import ActSettings, MessageSettings
from askui.models.shared.tools import ToolCollection
from askui.prompts.system import caesr_system_prompt

logger = logging.getLogger(__name__)


class RunnerRunService(RetrieveRunService, ABC):
    @abstractmethod
    def modify(
        self,
        workspace_id: WorkspaceId,
        thread_id: ThreadId,
        run_id: RunId,
        params: RunModify,
    ) -> Run:
        raise NotImplementedError


class Runner:
    def __init__(
        self,
        run_id: RunId,
        thread_id: ThreadId,
        workspace_id: WorkspaceId,
        assistant: Assistant,
        chat_history_manager: ChatHistoryManager,
        mcp_client_manager_manager: McpClientManagerManager,
        run_service: RunnerRunService,
        settings: Settings,
        last_message_id: MessageId,
        model: str | None = None,
    ) -> None:
        self._run_id = run_id
        self._workspace_id = workspace_id
        self._thread_id = thread_id
        self._assistant = assistant
        self._chat_history_manager = chat_history_manager
        self._mcp_client_manager_manager = mcp_client_manager_manager
        self._run_service = run_service
        self._settings = settings
        self._last_message_id = last_message_id
        self._model: str | None = model

    def _retrieve_run(self) -> Run:
        return self._run_service.retrieve(
            workspace_id=self._workspace_id,
            thread_id=self._thread_id,
            run_id=self._run_id,
        )

    def _modify_run(self, params: RunModify) -> Run:
        return self._run_service.modify(
            workspace_id=self._workspace_id,
            thread_id=self._thread_id,
            run_id=self._run_id,
            params=params,
        )

    def _build_system(self) -> list[BetaTextBlockParam]:
        metadata = {
            **self._get_run_extra_info(),
            "continued_by_user_at": datetime.now(timezone.utc).strftime(
                "%A, %B %d, %Y %H:%M:%S %z"
            ),
        }
        return [
            BetaTextBlockParam(
                type="text", text=caesr_system_prompt(self._assistant.name)
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
                workspace_id=self._workspace_id,
                thread_id=self._thread_id,
                assistant_id=self._assistant.id,
                run_id=self._run_id,
                message=on_message_cb_param.message,
                parent_id=self._last_message_id,
            )
            # Update the parent_id for the next message
            self._last_message_id = created_message.id
            await send_stream.send(
                MessageEvent(
                    data=created_message,
                    event="thread.message.created",
                )
            )
            updated_run = self._retrieve_run()
            if self._should_abort(updated_run):
                return None
            self._modify_run(RunPing())
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
            model = self._get_model()
            messages = syncify(self._chat_history_manager.retrieve_message_params)(
                workspace_id=self._workspace_id,
                thread_id=self._thread_id,
                tools=tools.to_params(),
                system=system,
                model=model,
            )
            custom_agent = CustomAgent()
            custom_agent.act(
                messages,
                model=model,
                on_message=on_message,
                tools=tools,
                settings=ActSettings(
                    messages=MessageSettings(
                        betas=betas,
                        system=system,
                        thinking={"type": "enabled", "budget_tokens": 4096},
                        max_tokens=8192,
                    ),
                ),
            )

        await asyncify(_run_agent_inner)()

    def _get_run_extra_info(self) -> dict[str, str]:
        return {
            "run_id": self._run_id,
            "thread_id": self._thread_id,
            "workspace_id": str(self._workspace_id),
            "assistant_id": self._assistant.id,
        }

    async def run(
        self,
        send_stream: ObjectStream[Event],
    ) -> None:
        try:
            updated_run = self._modify_run(RunStart())
            logger.info(
                "Run started",
                extra=self._get_run_extra_info(),
            )
            await send_stream.send(
                RunEvent(
                    data=updated_run,
                    event="thread.run.in_progress",
                )
            )
            await self._run_agent(send_stream=send_stream)
            updated_run = self._retrieve_run()
            if updated_run.status == "in_progress":
                self._modify_run(RunComplete())
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
                self._modify_run(RunCancel())
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
            logger.exception(
                "Run failed",
                extra=self._get_run_extra_info(),
            )
            updated_run = self._retrieve_run()
            self._modify_run(
                RunFail(last_error=RunError(message=str(e), code="server_error")),
            )
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

    def _should_abort(self, run: Run) -> bool:
        return run.status in ("cancelled", "cancelling", "expired")

    def _get_model(self) -> str:
        if self._model is not None:
            return self._model
        return self._settings.model
