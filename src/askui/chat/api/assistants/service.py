from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from askui.chat.api.models import ListQuery, ListResponse, UnixDatetime
from askui.chat.api.utils import generate_time_ordered_id


class Assistant(BaseModel):
    """An assistant that can be used in a thread."""

    id: str = Field(default_factory=lambda: generate_time_ordered_id("asst"))
    created_at: UnixDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    name: str | None = None
    description: str | None = None
    object: Literal["assistant"] = "assistant"


class CreateAssistantRequest(BaseModel):
    """Request model for creating an assistant."""

    name: str | None = None
    description: str | None = None


class AssistantModifyRequest(BaseModel):
    """Request model for updating an assistant."""

    name: str | None = None
    description: str | None = None


class AssistantService:
    """Service for managing assistants."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize assistant service.

        Args:
            base_dir: Base directory to store assistant data
        """
        self._base_dir = base_dir
        self._assistants_dir = base_dir / "assistants"

    def list_(self, query: ListQuery) -> ListResponse[Assistant]:
        """List all available assistants.

        Args:
            query (ListQuery): Query parameters for listing assistants

        Returns:
            ListResponse[Assistant]: ListResponse containing assistants sorted by creation date
        """
        if not self._assistants_dir.exists():
            return ListResponse(data=[])

        assistant_files = list(self._assistants_dir.glob("*.json"))
        assistants: list[Assistant] = []
        for f in assistant_files:
            with f.open("r") as file:
                assistants.append(Assistant.model_validate_json(file.read()))

        # Sort by creation date
        assistants = sorted(
            assistants, key=lambda a: a.created_at, reverse=(query.order == "desc")
        )

        # Apply before/after filters
        if query.after:
            assistants = [a for a in assistants if a.id > query.after]
        if query.before:
            assistants = [a for a in assistants if a.id < query.before]

        # Apply limit
        assistants = assistants[: query.limit]

        return ListResponse(
            data=assistants,
            first_id=assistants[0].id if assistants else None,
            last_id=assistants[-1].id if assistants else None,
            has_more=len(assistant_files) > query.limit,
        )

    def retrieve(self, assistant_id: str) -> Assistant:
        """Retrieve an assistant by ID.

        Args:
            assistant_id: ID of assistant to retrieve

        Returns:
            Assistant object

        Raises:
            FileNotFoundError: If assistant doesn't exist
        """
        assistant_file = self._assistants_dir / f"{assistant_id}.json"
        if not assistant_file.exists():
            error_msg = f"Assistant {assistant_id} not found"
            raise FileNotFoundError(error_msg)

        with assistant_file.open("r") as f:
            return Assistant.model_validate_json(f.read())

    def create(self, request: CreateAssistantRequest) -> Assistant:
        """Create a new assistant.

        Args:
            request: Assistant creation request

        Returns:
            Created assistant object
        """
        assistant = Assistant(
            name=request.name,
            description=request.description,
        )
        self._assistants_dir.mkdir(parents=True, exist_ok=True)
        assistant_file = self._assistants_dir / f"{assistant.id}.json"
        with assistant_file.open("w") as f:
            f.write(assistant.model_dump_json())
        return assistant

    def modify(self, assistant_id: str, request: AssistantModifyRequest) -> Assistant:
        """Update an existing assistant.

        Args:
            assistant_id: ID of assistant to modify
            request: Assistant modify request

        Returns:
            Updated assistant object

        Raises:
            FileNotFoundError: If assistant doesn't exist
        """
        assistant = self.retrieve(assistant_id)
        if request.name is not None:
            assistant.name = request.name
        if request.description is not None:
            assistant.description = request.description
        assistant_file = self._assistants_dir / f"{assistant_id}.json"
        with assistant_file.open("w") as f:
            f.write(assistant.model_dump_json())
        return assistant

    def delete(self, assistant_id: str) -> None:
        """Delete an assistant.

        Args:
            assistant_id: ID of assistant to delete

        Raises:
            FileNotFoundError: If assistant doesn't exist
        """
        assistant_file = self._assistants_dir / f"{assistant_id}.json"
        if not assistant_file.exists():
            error_msg = f"Assistant {assistant_id} not found"
            raise FileNotFoundError(error_msg)
        assistant_file.unlink()
