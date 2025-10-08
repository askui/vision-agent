from typing import Callable, Type

from askui.chat.api.models import WorkspaceId, WorkspaceResourceT


def build_workspace_filter_fn(
    workspace: WorkspaceId | None,
    resource_type: Type[WorkspaceResourceT],  # noqa: ARG001
) -> Callable[[WorkspaceResourceT], bool]:
    def filter_fn(resource: WorkspaceResourceT) -> bool:
        return resource.workspace_id is None or resource.workspace_id == workspace

    return filter_fn


def add_prefix(prefix: str, object_id: str) -> str:
    """Add prefix to ObjectId.

    Args:
        prefix (str): Prefix to add (e.g., "asst", "thread").
        object_id (str): ObjectId without prefix.

    Returns:
        str: Prefixed ID.
    """
    return f"{prefix}_{object_id}"


def remove_prefix(prefixed_id: str) -> str:
    """Remove prefix from ObjectId.

    Args:
        prefixed_id (str): Prefixed ID (e.g., "asst_507f1f77bcf86cd799439011").

    Returns:
        str: ObjectId without prefix.
    """
    return prefixed_id.split("_", 1)[1]
