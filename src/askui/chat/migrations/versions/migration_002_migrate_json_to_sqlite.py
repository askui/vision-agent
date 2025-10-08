"""Data migration from JSON/JSONL to SQLite."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from askui.chat.api.assistants.models import AssistantModel
from askui.chat.api.assistants.schemas import Assistant
from askui.chat.api.files.models import FileModel
from askui.chat.api.files.schemas import File as FilePydantic
from askui.chat.api.mcp_configs.models import McpConfigModel
from askui.chat.api.mcp_configs.schemas import McpConfig
from askui.chat.api.messages.models import MessageModel
from askui.chat.api.messages.schemas import Message
from askui.chat.api.runs.events.events import Event
from askui.chat.api.runs.events.models import EventModel
from askui.chat.api.runs.models import RunModel
from askui.chat.api.runs.schemas import Run
from askui.chat.api.threads.models import ThreadModel
from askui.chat.api.threads.schemas import Thread
from askui.chat.api.workflows.models import WorkflowModel, WorkflowTagModel
from askui.chat.api.workflows.schemas import Workflow
from askui.utils.datetime_utils import now
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def upgrade(engine, data_dir: Path):
    """Migrate data from JSON/JSONL to SQLite."""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Migrate assistants
        assistants_dir = data_dir / "assistants"
        if assistants_dir.exists():
            for json_file in assistants_dir.glob("*.json"):
                try:
                    assistant = Assistant.model_validate_json(json_file.read_text())
                    # Extract ObjectId from prefixed ID
                    object_id = assistant.id.split("_", 1)[1]

                    # Check if assistant already exists
                    existing = (
                        session.query(AssistantModel)
                        .filter(AssistantModel.id == object_id)
                        .first()
                    )
                    if existing:
                        logger.info(f"Assistant {object_id} already exists, skipping")
                        continue

                    db_assistant = AssistantModel(
                        id=object_id,
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
                    session.add(db_assistant)
                except Exception as e:
                    logger.warning(f"Failed to migrate assistant {json_file}: {e}")

        # Migrate threads
        threads_dir = data_dir / "threads"
        if threads_dir.exists():
            for json_file in threads_dir.glob("*.json"):
                try:
                    thread = Thread.model_validate_json(json_file.read_text())
                    object_id = thread.id.split("_", 1)[1]

                    # Check if thread already exists
                    existing = (
                        session.query(ThreadModel)
                        .filter(ThreadModel.id == object_id)
                        .first()
                    )
                    if existing:
                        logger.info(f"Thread {object_id} already exists, skipping")
                        continue

                    db_thread = ThreadModel(
                        id=object_id,
                        created_at=thread.created_at,
                        name=thread.name,
                    )
                    session.add(db_thread)
                except Exception as e:
                    logger.warning(f"Failed to migrate thread {json_file}: {e}")

        # Migrate files
        files_dir = data_dir / "files"
        if files_dir.exists():
            for json_file in files_dir.glob("*.json"):
                try:
                    file_data = json.loads(json_file.read_text())
                    # Handle incomplete file data from tests
                    if "size" not in file_data:
                        file_data["size"] = 0
                    if "media_type" not in file_data:
                        file_data["media_type"] = "application/octet-stream"
                    if "filename" not in file_data:
                        file_data["filename"] = "unknown"
                    if "created_at" not in file_data:
                        file_data["created_at"] = datetime.now(timezone.utc).isoformat()

                    file_model = FilePydantic.model_validate(file_data)
                    object_id = file_model.id.split("_", 1)[1]

                    # Check if file already exists
                    existing = (
                        session.query(FileModel)
                        .filter(FileModel.id == object_id)
                        .first()
                    )
                    if existing:
                        logger.info(f"File {object_id} already exists, skipping")
                        continue

                    db_file = FileModel(
                        id=object_id,
                        created_at=file_model.created_at,
                        filename=file_model.filename,
                        size=file_model.size,
                        media_type=file_model.media_type,
                    )
                    session.add(db_file)
                except Exception as e:
                    logger.warning(f"Failed to migrate file {json_file}: {e}")

        # Migrate MCP configs
        mcp_configs_dir = data_dir / "mcp_configs"
        if mcp_configs_dir.exists():
            for json_file in mcp_configs_dir.glob("*.json"):
                try:
                    mcp_config = McpConfig.model_validate_json(json_file.read_text())
                    object_id = mcp_config.id.split("_", 1)[1]

                    # Check if MCP config already exists
                    existing = (
                        session.query(McpConfigModel)
                        .filter(McpConfigModel.id == object_id)
                        .first()
                    )
                    if existing:
                        logger.info(f"MCP config {object_id} already exists, skipping")
                        continue

                    db_mcp_config = McpConfigModel(
                        id=object_id,
                        workspace_id=str(mcp_config.workspace_id)
                        if mcp_config.workspace_id
                        else None,
                        created_at=mcp_config.created_at,
                        name=mcp_config.name,
                        mcp_server=mcp_config.mcp_server.model_dump(),
                    )
                    session.add(db_mcp_config)
                except Exception as e:
                    logger.warning(f"Failed to migrate MCP config {json_file}: {e}")

        # Migrate workflows with tags
        workflows_dir = data_dir / "workflows"
        if workflows_dir.exists():
            for json_file in workflows_dir.glob("*.json"):
                workflow = Workflow.model_validate_json(json_file.read_text())
                object_id = workflow.id.split("_", 1)[1]
                db_workflow = WorkflowModel(
                    id=object_id,
                    workspace_id=str(workflow.workspace_id)
                    if workflow.workspace_id
                    else None,
                    created_at=workflow.created_at,
                    name=workflow.name,
                    description=workflow.description,
                )
                session.add(db_workflow)

                # Add tags
                for tag in workflow.tags:
                    db_tag = WorkflowTagModel(workflow_id=object_id, tag=tag)
                    session.add(db_tag)

        # Migrate messages
        messages_dir = data_dir / "messages"
        if messages_dir.exists():
            for thread_dir in messages_dir.iterdir():
                if thread_dir.is_dir():
                    thread_id = thread_dir.name.split("_", 1)[1]  # Remove prefix
                    for json_file in thread_dir.glob("*.json"):
                        message = Message.model_validate_json(json_file.read_text())
                        object_id = message.id.split("_", 1)[1]
                        db_message = MessageModel(
                            id=object_id,
                            thread_id=thread_id,
                            created_at=message.created_at,
                            assistant_id=message.assistant_id.split("_", 1)[1]
                            if message.assistant_id
                            else None,
                            run_id=message.run_id.split("_", 1)[1]
                            if message.run_id
                            else None,
                            role=message.role,
                            content=message.content,
                            stop_reason=message.stop_reason,
                        )
                        session.add(db_message)

        # Migrate runs
        runs_dir = data_dir / "runs"
        if runs_dir.exists():
            for thread_dir in runs_dir.iterdir():
                if thread_dir.is_dir():
                    thread_id = thread_dir.name.split("_", 1)[1]  # Remove prefix
                    for json_file in thread_dir.glob("*.json"):
                        run = Run.model_validate_json(json_file.read_text())
                        object_id = run.id.split("_", 1)[1]
                        db_run = RunModel(
                            id=object_id,
                            thread_id=thread_id,
                            assistant_id=run.assistant_id.split("_", 1)[1],
                            created_at=run.created_at,
                            started_at=run.started_at,
                            completed_at=run.completed_at,
                            failed_at=run.failed_at,
                            cancelled_at=run.cancelled_at,
                            tried_cancelling_at=run.tried_cancelling_at,
                            expires_at=run.expires_at,
                            last_error=run.last_error.model_dump()
                            if run.last_error
                            else None,
                        )
                        session.add(db_run)

        # Migrate events from JSONL
        events_dir = data_dir / "events"
        if events_dir.exists():
            for thread_dir in events_dir.iterdir():
                if thread_dir.is_dir():
                    thread_id = thread_dir.name.split("_", 1)[1]  # Remove prefix
                    for jsonl_file in thread_dir.glob("*.jsonl"):
                        run_id = jsonl_file.stem.split("_", 1)[1]  # Remove prefix
                        sequence_num = 0
                        with open(jsonl_file) as f:
                            for line in f:
                                event_json = line.strip()
                                if event_json:
                                    # Parse and insert event
                                    try:
                                        event = Event.model_validate_json(event_json)
                                        db_event = EventModel(
                                            run_id=run_id,
                                            thread_id=thread_id,
                                            sequence_num=sequence_num,
                                            event_type=event.event,
                                            event_data=event_json,
                                            created_at=now(),
                                        )
                                        session.add(db_event)
                                        sequence_num += 1
                                    except Exception:
                                        # Skip invalid events
                                        continue

        session.commit()

        # After successful migration, rename JSON directories
        for dir_name in [
            "assistants",
            "threads",
            "messages",
            "runs",
            "files",
            "mcp_configs",
            "workflows",
            "events",
        ]:
            dir_path = data_dir / dir_name
            if dir_path.exists():
                dir_path.rename(data_dir / f"{dir_name}.migrated")

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        session.close()
