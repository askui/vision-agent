from askui.chat.api.dependencies import SessionFactoryDep
from askui.chat.api.messages.dependencies import MessageServiceDep
from askui.chat.api.messages.service import MessageService
from askui.chat.api.runs.dependencies import RunServiceDep
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.facade import ThreadFacade
from askui.chat.api.threads.service import ThreadService
from fastapi import Depends


def get_thread_service(
    session_factory=SessionFactoryDep,
    message_service: MessageService = MessageServiceDep,
    run_service: RunService = RunServiceDep,
) -> ThreadService:
    """Get ThreadService instance."""
    return ThreadService(
        session_factory=session_factory,
        message_service=message_service,
        run_service=run_service,
    )


ThreadServiceDep = Depends(get_thread_service)


def get_thread_facade(
    thread_service: ThreadService = ThreadServiceDep,
    message_service: MessageService = MessageServiceDep,
    run_service: RunService = RunServiceDep,
) -> ThreadFacade:
    return ThreadFacade(
        thread_service=thread_service,
        message_service=message_service,
        run_service=run_service,
    )


ThreadFacadeDep = Depends(get_thread_facade)
