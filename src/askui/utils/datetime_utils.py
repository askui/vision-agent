from datetime import datetime, timezone
from typing import Annotated

from pydantic import AwareDatetime, PlainSerializer

UnixDatetime = Annotated[
    AwareDatetime,
    PlainSerializer(
        lambda v: int(v.timestamp()),
        return_type=int,
        when_used="json-unless-none",
    ),
]


def now() -> AwareDatetime:
    return datetime.now(tz=timezone.utc)
