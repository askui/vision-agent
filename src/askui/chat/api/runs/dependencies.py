from pathlib import Path

from fastapi import Depends

from askui.chat.api.dependencies import WorkspaceDirDep

from .service import RunService


def get_runs_service(workspace_dir: Path = WorkspaceDirDep) -> RunService:
    """Get RunService instance."""
    return RunService(workspace_dir)


RunServiceDep = Depends(get_runs_service)
