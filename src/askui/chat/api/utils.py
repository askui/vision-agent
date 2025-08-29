from typing import Callable, Type

from askui.chat.api.models import WorkspaceId, WorkspaceResourceT


def build_workspace_filter_fn(
    workspace: WorkspaceId | None,
    resource_type: Type[WorkspaceResourceT],  # noqa: ARG001
) -> Callable[[WorkspaceResourceT], bool]:
    def filter_fn(resource: WorkspaceResourceT) -> bool:
        return resource.workspace_id is None or resource.workspace_id == workspace

    return filter_fn
