"""Assistant database model."""

from datetime import datetime, timezone

from askui.chat.api.assistants.schemas import Assistant, AssistantCreateParams
from askui.chat.api.db.base import Base
from askui.chat.api.db.types import AssistantId
from bson import ObjectId
from sqlalchemy import JSON, Column, DateTime, String, Text


class AssistantModel(Base):
    """Assistant database model."""

    __tablename__ = "assistants"
    id = Column(AssistantId, primary_key=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    avatar = Column(Text, nullable=True)
    tools = Column(JSON, nullable=False)
    system = Column(Text, nullable=True)

    @staticmethod
    def create_id() -> str:
        """Create a new assistant ID with prefix."""
        return f"asst_{ObjectId()}"

    def to_pydantic(self) -> Assistant:
        """Convert to Pydantic model."""
        # Ensure created_at is timezone-aware
        created_at = self.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        return Assistant(
            id=self.id,  # Prefix is handled by the specialized type
            workspace_id=self.workspace_id,
            created_at=created_at,
            name=self.name,
            description=self.description,
            avatar=self.avatar,
            tools=self.tools,
            system=self.system,
        )

    @classmethod
    def from_pydantic(cls, assistant: Assistant) -> "AssistantModel":
        """Create from Pydantic model."""
        return cls(
            id=assistant.id,
            workspace_id=str(assistant.workspace_id)
            if assistant.workspace_id
            else None,
            created_at=assistant.created_at,
            name=assistant.name,
            description=assistant.description,
            avatar=assistant.avatar,
            tools=assistant.tools,
            system=assistant.system,
        )

    @classmethod
    def from_create_params(
        cls, params: AssistantCreateParams, workspace_id: str | None = None
    ) -> "AssistantModel":
        """Create from create parameters."""
        return cls(
            id=cls.create_id(),
            workspace_id=str(workspace_id) if workspace_id else None,
            created_at=datetime.now(timezone.utc),
            name=params.name,
            description=params.description,
            avatar=params.avatar,
            tools=params.tools,
            system=params.system,
        )
