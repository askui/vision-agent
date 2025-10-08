"""Integration tests for database migrations."""

from datetime import datetime, timezone
from pathlib import Path

from askui.chat.api.assistants.models import Assistant
from askui.chat.api.workflows.models import Workflow
from askui.chat.migrations import MigrationRunner


def test_migration_from_empty_db(tmp_path: Path):
    """Test migration from empty database."""
    db_path = tmp_path / "test.db"
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    runner = MigrationRunner(db_path)

    # Should need migration for empty database (version 0 -> 2)
    assert runner.should_migrate(data_dir)

    # Run migration
    runner.migrate(data_dir)

    # Check that schema version was recorded
    assert runner.get_current_version() == 2


def test_migration_with_json_files(tmp_path: Path):
    """Test migration with existing JSON files."""
    db_path = tmp_path / "test.db"
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create sample JSON files
    assistants_dir = data_dir / "assistants"
    assistants_dir.mkdir()

    assistant = Assistant(
        id="asst_507f1f77bcf86cd799439011",
        workspace_id="test-workspace",
        created_at=datetime.now(timezone.utc),
        name="Test Assistant",
        description="Test description",
        avatar=None,
        tools=["test_tool"],
        system="Test system",
    )

    assistant_file = assistants_dir / "asst_507f1f77bcf86cd799439011.json"
    assistant_file.write_text(assistant.model_dump_json())

    # Create workflow with tags
    workflows_dir = data_dir / "workflows"
    workflows_dir.mkdir()

    workflow = Workflow(
        id="workflow_507f1f77bcf86cd799439012",
        workspace_id="test-workspace",
        created_at=datetime.now(timezone.utc),
        name="Test Workflow",
        description="Test description",
        tags=["automation", "testing"],
    )

    workflow_file = workflows_dir / "workflow_507f1f77bcf86cd799439012.json"
    workflow_file.write_text(workflow.model_dump_json())

    runner = MigrationRunner(db_path)

    # Should need migration
    assert runner.should_migrate(data_dir)

    # Run migration
    runner.migrate(data_dir)

    # Check that schema version was recorded
    assert runner.get_current_version() == 2

    # Check that JSON directories were renamed
    assert (data_dir / "assistants.migrated").exists()
    assert (data_dir / "workflows.migrated").exists()
    assert not (data_dir / "assistants").exists()
    assert not (data_dir / "workflows").exists()


def test_migration_idempotent(tmp_path: Path):
    """Test that migration is idempotent."""
    db_path = tmp_path / "test.db"
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    runner = MigrationRunner(db_path)

    # Run migration twice
    runner.migrate(data_dir)
    version_after_first = runner.get_current_version()

    runner.migrate(data_dir)
    version_after_second = runner.get_current_version()

    # Should be the same version
    assert version_after_first == version_after_second == 2


def test_workflow_tags_migration(tmp_path: Path):
    """Test migration of workflow tags to separate table."""
    db_path = tmp_path / "test.db"
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create workflow with tags
    workflows_dir = data_dir / "workflows"
    workflows_dir.mkdir()

    workflow = Workflow(
        id="workflow_507f1f77bcf86cd799439012",
        workspace_id="test-workspace",
        created_at=datetime.now(timezone.utc),
        name="Test Workflow",
        description="Test description",
        tags=["automation", "testing", "deployment"],
    )

    workflow_file = workflows_dir / "workflow_507f1f77bcf86cd799439012.json"
    workflow_file.write_text(workflow.model_dump_json())

    runner = MigrationRunner(db_path)
    runner.migrate(data_dir)

    # Check that tags were migrated to separate table
    from sqlalchemy import create_engine, text

    engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as conn:
        # Check workflow_tags table
        result = conn.execute(
            text(
                "SELECT * FROM workflow_tags WHERE workflow_id = '507f1f77bcf86cd799439012'"
            )
        )
        tags = [row[2] for row in result]  # tag column is index 2

        assert len(tags) == 3
        assert "automation" in tags
        assert "testing" in tags
        assert "deployment" in tags


def test_objectid_prefix_preserved(tmp_path: Path):
    """Test that ObjectId prefixes are preserved during migration."""
    db_path = tmp_path / "test.db"
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create assistant with prefixed ID
    assistants_dir = data_dir / "assistants"
    assistants_dir.mkdir()

    assistant = Assistant(
        id="asst_507f1f77bcf86cd799439011",
        workspace_id="test-workspace",
        created_at=datetime.now(timezone.utc),
        name="Test Assistant",
        description="Test description",
        avatar=None,
        tools=["test_tool"],
        system="Test system",
    )

    assistant_file = assistants_dir / "asst_507f1f77bcf86cd799439011.json"
    assistant_file.write_text(assistant.model_dump_json())

    runner = MigrationRunner(db_path)
    runner.migrate(data_dir)

    # Check that ObjectId was stored without prefix in DB
    from sqlalchemy import create_engine, text

    engine = create_engine(f"sqlite:///{db_path}")

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM assistants WHERE id = '507f1f77bcf86cd799439011'")
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "507f1f77bcf86cd799439011"  # No prefix in DB
