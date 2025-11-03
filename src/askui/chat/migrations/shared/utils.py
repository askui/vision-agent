from datetime import datetime, timezone
from typing import Callable

from pydantic import AwareDatetime


def now_v1() -> AwareDatetime:
    return datetime.now(tz=timezone.utc)


def build_prefixer(prefix: str) -> Callable[[str], str]:
    def prefixer(id_: str) -> str:
        if id_.startswith(prefix):
            return id_
        return f"{prefix}_{id_}"

    return prefixer
