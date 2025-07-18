from datetime import datetime, timezone
from typing import Annotated

from pydantic import AwareDatetime, PlainSerializer

UnixDatetime = Annotated[
    AwareDatetime,
    PlainSerializer(
        lambda v: int(v.timestamp()),
        return_type=int,
    ),
]


def now() -> AwareDatetime:
    return datetime.now(tz=timezone.utc)
