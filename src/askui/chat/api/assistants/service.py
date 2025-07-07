from pathlib import Path

from pydantic import BaseModel, Field

from askui.chat.api.assistants.models import Assistant
from askui.chat.api.assistants.seeds import SEEDS
from askui.chat.api.models import DO_NOT_PATCH, DoNotPatch, ListQuery, ListResponse


class CreateAssistantRequest(BaseModel):
    """Request model for creating an assistant."""

    name: str | None = None
    description: str | None = None
    avatar: str | None = Field(default=None, description="URL of the avatar image")


class AssistantModifyRequest(BaseModel):
    """Request model for updating an assistant."""

    name: str | None | DoNotPatch = DO_NOT_PATCH
    description: str | None | DoNotPatch = DO_NOT_PATCH
    avatar: str | None | DoNotPatch = Field(
        default=DO_NOT_PATCH, description="URL of the avatar image"
    )


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
            ListResponse[Assistant]: ListResponse containing assistants sorted by
                creation date
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
        self._save(assistant)
        return assistant

    def _save(self, assistant: Assistant) -> None:
        """Save an assistant to the file system."""
        self._assistants_dir.mkdir(parents=True, exist_ok=True)
        assistant_file = self._assistants_dir / f"{assistant.id}.json"
        with assistant_file.open("w") as f:
            f.write(assistant.model_dump_json())

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
        if not isinstance(request.name, DoNotPatch):
            assistant.name = request.name
        if not isinstance(request.description, DoNotPatch):
            assistant.description = request.description
        if not isinstance(request.avatar, DoNotPatch):
            assistant.avatar = request.avatar
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

    def seed(self) -> None:
        """Seed the assistant service with default assistants."""
        for seed in SEEDS:
            self._save(seed)
