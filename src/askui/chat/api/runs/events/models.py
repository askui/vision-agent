"""Event database model."""

from askui.chat.api.db.base import Base
from askui.chat.api.db.types import RunId, ThreadId
from askui.chat.api.runs.events.events import Event
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String


class EventModel(Base):
    """Event database model."""

    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        RunId,
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    thread_id = Column(ThreadId, nullable=False, index=True)
    sequence_num = Column(Integer, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, index=True)

    __table_args__ = (Index("idx_events_run_sequence", "run_id", "sequence_num"),)

    def to_pydantic(self) -> Event:
        """Convert to Pydantic model."""
        # Parse the event data JSON to create Event object
        return Event.model_validate_json(self.event_data)

    @classmethod
    def from_pydantic(
        cls, event: Event, run_id: str, thread_id: str, sequence_num: int
    ) -> "EventModel":
        """Create from Pydantic model."""
        return cls(
            run_id=run_id,
            thread_id=thread_id,
            sequence_num=sequence_num,
            event_type=event.event,
            event_data=event.model_dump_json(),
            created_at=event.created_at,
        )
