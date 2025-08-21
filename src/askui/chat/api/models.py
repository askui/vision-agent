from typing import Annotated

from askui.utils.id_utils import IdField

AssistantId = Annotated[str, IdField("asst")]
McpConfigId = Annotated[str, IdField("mcpcnf")]
FileId = Annotated[str, IdField("file")]
MessageId = Annotated[str, IdField("msg")]
RunId = Annotated[str, IdField("run")]
ThreadId = Annotated[str, IdField("thread")]
