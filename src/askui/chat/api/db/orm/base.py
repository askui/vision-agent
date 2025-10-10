"""SQLAlchemy declarative base."""

from typing import Any

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from typing_extensions import Self


class Base(MappedAsDataclass, DeclarativeBase):
    def update(self, values: dict[str, Any]) -> Self:
        for key, value in values.items():
            setattr(self, key, value)
        return self
