from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from askui.chat.api.utils import generate_time_ordered_id


class Assistant(BaseModel):
    """An assistant that can be used in a thread."""

    id: str = Field(default_factory=lambda: generate_time_ordered_id("asst"))
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    name: str | None = None
    description: str | None = None
    object: Literal["assistant"] = "assistant"


class AssistantListResponse(BaseModel):
    """Response model for listing assistants."""

    object: Literal["list"] = "list"
    data: list[Assistant]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class CreateAssistantRequest(BaseModel):
    """Request model for creating an assistant."""

    name: str | None = None
    description: str | None = None


class UpdateAssistantRequest(BaseModel):
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

    def list_(self, limit: int | None = None) -> AssistantListResponse:
        """List all available assistants.

        Args:
            limit: Optional maximum number of assistants to return

        Returns:
            AssistantListResponse containing assistants sorted by creation date (newest first)
        """
        if not self._assistants_dir.exists():
            return AssistantListResponse(data=[])

        assistant_files = list(self._assistants_dir.glob("*.json"))
        assistants: list[Assistant] = []
        for f in assistant_files:
            with f.open("r") as file:
                assistants.append(Assistant.model_validate_json(file.read()))

        # Sort by creation date, newest first
        assistants = sorted(assistants, key=lambda a: a.created_at, reverse=True)

        # Apply limit if specified
        if limit is not None:
            assistants = assistants[:limit]

        return AssistantListResponse(
            data=assistants,
            first_id=assistants[0].id if assistants else None,
            last_id=assistants[-1].id if assistants else None,
            has_more=len(assistant_files) > (limit or len(assistant_files)),
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

    def update(self, assistant_id: str, request: UpdateAssistantRequest) -> Assistant:
        """Update an existing assistant.

        Args:
            assistant_id: ID of assistant to update
            request: Assistant update request

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
