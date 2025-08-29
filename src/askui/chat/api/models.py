from typing import Annotated, TypeVar

from pydantic import UUID4

from askui.utils.api_utils import Resource
from askui.utils.id_utils import IdField

AssistantId = Annotated[str, IdField("asst")]
McpConfigId = Annotated[str, IdField("mcpcnf")]
FileId = Annotated[str, IdField("file")]
MessageId = Annotated[str, IdField("msg")]
RunId = Annotated[str, IdField("run")]
ThreadId = Annotated[str, IdField("thread")]
WorkspaceId = UUID4


class WorkspaceResource(Resource):
    workspace_id: WorkspaceId | None = None


WorkspaceResourceT = TypeVar("WorkspaceResourceT", bound=WorkspaceResource)
