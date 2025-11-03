from fastapi import Depends

from askui.chat.api.db.session import SessionDep
from askui.chat.api.runs.dependencies import RunServiceDep
from askui.chat.api.runs.service import RunService
from askui.chat.api.threads.facade import ThreadFacade
from askui.chat.api.threads.service import ThreadService


def get_thread_service(
    session: SessionDep,
) -> ThreadService:
    """Get ThreadService instance."""
    return ThreadService(session=session)


ThreadServiceDep = Depends(get_thread_service)


def get_thread_facade(
    thread_service: ThreadService = ThreadServiceDep,
    run_service: RunService = RunServiceDep,
) -> ThreadFacade:
    return ThreadFacade(
        thread_service=thread_service,
        run_service=run_service,
    )


ThreadFacadeDep = Depends(get_thread_facade)
