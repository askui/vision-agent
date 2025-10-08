"""Message database model."""

from askui.chat.api.db.base import Base
from askui.chat.api.db.types import AssistantId, MessageId, RunId, ThreadId
from askui.chat.api.messages.schemas import Message
from sqlalchemy import JSON, Column, DateTime, ForeignKey, String


class MessageModel(Base):
    """Message database model."""

    __tablename__ = "messages"
    id = Column(MessageId, primary_key=True)
    thread_id = Column(
        ThreadId,
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, index=True)
    assistant_id = Column(
        AssistantId,
        ForeignKey("assistants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    run_id = Column(
        RunId,
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    stop_reason = Column(String, nullable=True)

    def to_pydantic(self) -> Message:
        """Convert to Pydantic model."""
        return Message(
            id=self.id,  # Prefix is handled by the specialized type
            thread_id=self.thread_id,
            created_at=self.created_at,
            assistant_id=self.assistant_id,
            run_id=self.run_id,
            role=self.role,
            content=self.content,
            stop_reason=self.stop_reason,
        )

    @classmethod
    def from_pydantic(cls, message: Message) -> "MessageModel":
        """Create from Pydantic model."""
        return cls(
            id=message.id,
            thread_id=message.thread_id,
            created_at=message.created_at,
            assistant_id=message.assistant_id,
            run_id=message.run_id,
            role=message.role,
            content=message.content,
            stop_reason=message.stop_reason,
        )
