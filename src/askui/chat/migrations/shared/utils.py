from datetime import datetime, timezone

from pydantic import AwareDatetime


def now_v1() -> AwareDatetime:
    return datetime.now(tz=timezone.utc)
