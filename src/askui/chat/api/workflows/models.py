"""Workflow database models."""

from askui.chat.api.db.base import Base
from askui.chat.api.db.types import WorkflowId
from askui.chat.api.workflows.schemas import Workflow
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship


class WorkflowModel(Base):
    """Workflow database model."""

    __tablename__ = "workflows"
    id = Column(WorkflowId, primary_key=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    # Relationship to tags
    tags = relationship(
        "WorkflowTagModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def to_pydantic(self) -> Workflow:
        """Convert to Pydantic model."""
        data = {
            "id": self.id,  # Prefix is handled by the specialized type
            "workspace_id": self.workspace_id,
            "created_at": self.created_at,
            "name": self.name,
            "description": self.description,
            "tags": [tag.tag for tag in self.tags],
        }
        return Workflow.model_validate(data)

    @classmethod
    def from_pydantic(cls, workflow: Workflow) -> "WorkflowModel":
        """Create from Pydantic model."""
        return cls(
            id=workflow.id,
            workspace_id=str(workflow.workspace_id) if workflow.workspace_id else None,
            created_at=workflow.created_at,
            name=workflow.name,
            description=workflow.description,
        )


class WorkflowTagModel(Base):
    """Workflow tag database model."""

    __tablename__ = "workflow_tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(
        WorkflowId,
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag = Column(String, nullable=False, index=True)
    workflow = relationship("WorkflowModel", back_populates="tags")

    __table_args__ = (Index("idx_workflow_tags_tag_workflow", "tag", "workflow_id"),)
