"""Run database model."""

from askui.chat.api.db.base import Base
from askui.chat.api.db.types import AssistantId, RunId, ThreadId
from askui.chat.api.runs.schemas import Run
from sqlalchemy import JSON, Column, DateTime, ForeignKey


class RunModel(Base):
    """Run database model."""

    __tablename__ = "runs"
    id = Column(RunId, primary_key=True)
    thread_id = Column(
        ThreadId,
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assistant_id = Column(
        AssistantId,
        ForeignKey("assistants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    tried_cancelling_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    last_error = Column(JSON, nullable=True)

    def to_pydantic(self) -> Run:
        """Convert to Pydantic model."""
        data = {
            "id": self.id,  # Prefix is handled by the specialized type
            "thread_id": self.thread_id,
            "assistant_id": self.assistant_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "failed_at": self.failed_at,
            "cancelled_at": self.cancelled_at,
            "tried_cancelling_at": self.tried_cancelling_at,
            "expires_at": self.expires_at,
            "last_error": self.last_error,
        }
        return Run.model_validate(data)

    @classmethod
    def from_pydantic(cls, run: Run) -> "RunModel":
        """Create from Pydantic model."""
        return cls(
            id=run.id,
            thread_id=run.thread_id,
            assistant_id=run.assistant_id,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            failed_at=run.failed_at,
            cancelled_at=run.cancelled_at,
            tried_cancelling_at=run.tried_cancelling_at,
            expires_at=run.expires_at,
            last_error=run.last_error.model_dump() if run.last_error else None,
        )
