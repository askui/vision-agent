from fastapi import Depends
from pydantic import BaseModel

from askui.utils.api_utils import ListQuery

AssistantId = str
McpConfigId = str
FileId = str
MessageId = str
RunId = str
ThreadId = str


ListQueryDep = Depends(ListQuery)


class DoNotPatch(BaseModel):
    pass


DO_NOT_PATCH = DoNotPatch()
