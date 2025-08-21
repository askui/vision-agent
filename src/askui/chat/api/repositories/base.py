from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from askui.utils.api_utils import ListQuery, ListResponse

T = TypeVar("T", bound=BaseModel)
K = TypeVar("K")


class BaseRepository(ABC, Generic[T, K]):
    """Base repository interface for CRUD operations."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""

    @abstractmethod
    async def find_one(self, entity_id: K) -> T:
        """Retrieve an entity by ID."""

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""

    @abstractmethod
    async def delete(self, entity_id: K) -> None:
        """Delete an entity by ID."""

    @abstractmethod
    async def find(self, query: ListQuery, **filters: Any) -> ListResponse[T]:
        """List entities with optional filtering."""

    @abstractmethod
    async def exists(self, entity_id: K) -> bool:
        """Check if entity exists."""
