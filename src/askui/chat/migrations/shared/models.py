from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, PlainSerializer

UnixDatetimeV1 = Annotated[
    AwareDatetime,
    PlainSerializer(
        lambda v: int(v.timestamp()),
        return_type=int,
    ),
]
WorkspaceIdV1 = UUID
