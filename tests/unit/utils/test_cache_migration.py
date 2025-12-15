"""Tests for cache migration utilities."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from askui.utils.cache_migration import CacheMigration, CacheMigrationError


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "caches"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def v1_cache_data() -> list[dict[str, Any]]:
    """Sample v0.0 cache data (just a trajectory list)."""
    return [
        {"id": "1", "name": "click", "input": {"x": 100}, "type": "tool_use"},
        {"id": "2", "name": "type", "input": {"text": "test"}, "type": "tool_use"},
    ]


@pytest.fixture
def v2_cache_data() -> dict[str, Any]:
    """Sample v0.1 cache data (with metadata)."""
    return {
        "metadata": {
            "version": "0.1",
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "execution_attempts": 0,
            "last_executed_at": None,
            "failures": [],
            "is_valid": True,
            "invalidation_reason": None,
        },
        "trajectory": [
            {"id": "1", "name": "click", "input": {"x": 100}, "type": "tool_use"},
        ],
        "placeholders": {},
    }


# Initialization Tests


def test_cache_migration_initialization() -> None:
    """Test CacheMigration initializes with correct defaults."""
    migration = CacheMigration()
    assert migration.backup is False
    assert migration.backup_suffix == ".v1.backup"
    assert migration.migrated_count == 0
    assert migration.skipped_count == 0
    assert migration.error_count == 0


def test_cache_migration_initialization_with_backup() -> None:
    """Test CacheMigration initializes with backup enabled."""
    migration = CacheMigration(backup=True, backup_suffix=".bak")
    assert migration.backup is True
    assert migration.backup_suffix == ".bak"


# Single File Migration Tests


def test_migrate_file_v1_to_v2(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test migrating a v0.0 cache file to v0.1."""
    cache_file = temp_cache_dir / "test.json"
    with cache_file.open("w") as f:
        json.dump(v1_cache_data, f)

    migration = CacheMigration()
    success, message = migration.migrate_file(cache_file, dry_run=False)

    assert success is True
    assert "Migrated" in message

    # Verify file was updated to v0.1
    with cache_file.open("r") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert "metadata" in data
    assert data["metadata"]["version"] == "0.1"
    assert "trajectory" in data
    assert "placeholders" in data


def test_migrate_file_already_v2(
    temp_cache_dir: Path, v2_cache_data: dict[str, Any]
) -> None:
    """Test that v0.1 files are skipped."""
    cache_file = temp_cache_dir / "test.json"
    with cache_file.open("w") as f:
        json.dump(v2_cache_data, f)

    migration = CacheMigration()
    success, message = migration.migrate_file(cache_file, dry_run=False)

    assert success is False
    assert "Already v0.1" in message


def test_migrate_file_dry_run(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test dry run doesn't modify files."""
    cache_file = temp_cache_dir / "test.json"
    with cache_file.open("w") as f:
        json.dump(v1_cache_data, f)

    # Store original content
    original_content = cache_file.read_text()

    migration = CacheMigration()
    success, message = migration.migrate_file(cache_file, dry_run=True)

    assert success is True
    assert "Would migrate" in message

    # Verify file wasn't modified
    assert cache_file.read_text() == original_content


def test_migrate_file_creates_backup(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test that backup is created when requested."""
    cache_file = temp_cache_dir / "test.json"
    with cache_file.open("w") as f:
        json.dump(v1_cache_data, f)

    migration = CacheMigration(backup=True, backup_suffix=".backup")
    success, message = migration.migrate_file(cache_file, dry_run=False)

    assert success is True

    # Verify backup exists
    backup_file = temp_cache_dir / "test.json.backup"
    assert backup_file.exists()

    # Verify backup contains original v0.0 data
    with backup_file.open("r") as f:
        backup_data = json.load(f)
    assert backup_data == v1_cache_data


def test_migrate_file_not_found(temp_cache_dir: Path) -> None:
    """Test handling of missing file."""
    cache_file = temp_cache_dir / "nonexistent.json"

    migration = CacheMigration()
    success, message = migration.migrate_file(cache_file, dry_run=False)

    assert success is False
    assert "File not found" in message


def test_migrate_file_invalid_json(temp_cache_dir: Path) -> None:
    """Test handling of invalid JSON."""
    cache_file = temp_cache_dir / "invalid.json"
    cache_file.write_text("not valid json{")

    migration = CacheMigration()
    success, message = migration.migrate_file(cache_file, dry_run=False)

    assert success is False
    assert "Error" in message


# Directory Migration Tests


def test_migrate_directory_multiple_files(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test migrating multiple files in a directory."""
    # Create several v0.0 cache files
    for i in range(3):
        cache_file = temp_cache_dir / f"cache_{i}.json"
        with cache_file.open("w") as f:
            json.dump(v1_cache_data, f)

    migration = CacheMigration()
    stats = migration.migrate_directory(temp_cache_dir, dry_run=False)

    assert stats["total"] == 3
    assert stats["migrated"] == 3
    assert stats["skipped"] == 0
    assert stats["errors"] == 0


def test_migrate_directory_mixed_versions(
    temp_cache_dir: Path,
    v1_cache_data: list[dict[str, Any]],
    v2_cache_data: dict[str, Any],
) -> None:
    """Test migrating directory with mixed v0.0 and v0.1 files."""
    # Create v0.0 files
    for i in range(2):
        cache_file = temp_cache_dir / f"v1_cache_{i}.json"
        with cache_file.open("w") as f:
            json.dump(v1_cache_data, f)

    # Create v0.1 files
    for i in range(2):
        cache_file = temp_cache_dir / f"v2_cache_{i}.json"
        with cache_file.open("w") as f:
            json.dump(v2_cache_data, f)

    migration = CacheMigration()
    stats = migration.migrate_directory(temp_cache_dir, dry_run=False)

    assert stats["total"] == 4
    assert stats["migrated"] == 2  # Only v0.0 files migrated
    assert stats["skipped"] == 2  # v0.1 files skipped
    assert stats["errors"] == 0


def test_migrate_directory_dry_run(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test dry run on directory doesn't modify files."""
    cache_file = temp_cache_dir / "test.json"
    with cache_file.open("w") as f:
        json.dump(v1_cache_data, f)

    original_content = cache_file.read_text()

    migration = CacheMigration()
    stats = migration.migrate_directory(temp_cache_dir, dry_run=True)

    assert stats["migrated"] == 1
    # Verify file wasn't modified
    assert cache_file.read_text() == original_content


def test_migrate_directory_with_pattern(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test migrating directory with custom file pattern."""
    # Create files with different extensions
    for ext in ["json", "cache", "txt"]:
        cache_file = temp_cache_dir / f"test.{ext}"
        with cache_file.open("w") as f:
            json.dump(v1_cache_data, f)

    migration = CacheMigration()
    stats = migration.migrate_directory(
        temp_cache_dir, file_pattern="*.cache", dry_run=False
    )

    # Only .cache file should be processed
    assert stats["total"] == 1
    assert stats["migrated"] == 1


def test_migrate_directory_not_found() -> None:
    """Test handling of non-existent directory."""
    migration = CacheMigration()

    with pytest.raises(CacheMigrationError, match="Directory not found"):
        migration.migrate_directory(Path("/nonexistent/directory"))


def test_migrate_directory_empty(temp_cache_dir: Path) -> None:
    """Test migrating empty directory."""
    migration = CacheMigration()
    stats = migration.migrate_directory(temp_cache_dir, dry_run=False)

    assert stats["total"] == 0
    assert stats["migrated"] == 0
    assert stats["skipped"] == 0
    assert stats["errors"] == 0


def test_migrate_directory_with_errors(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test directory migration handles errors gracefully."""
    # Create valid v0.0 file
    valid_file = temp_cache_dir / "valid.json"
    with valid_file.open("w") as f:
        json.dump(v1_cache_data, f)

    # Create invalid file
    invalid_file = temp_cache_dir / "invalid.json"
    invalid_file.write_text("not valid json{")

    migration = CacheMigration()
    stats = migration.migrate_directory(temp_cache_dir, dry_run=False)

    assert stats["total"] == 2
    assert stats["migrated"] == 1  # Valid file migrated
    assert stats["errors"] == 1  # Invalid file failed
    assert stats["skipped"] == 0


def test_migrate_directory_creates_backups(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test directory migration creates backups for all files."""
    # Create v0.0 files
    for i in range(2):
        cache_file = temp_cache_dir / f"cache_{i}.json"
        with cache_file.open("w") as f:
            json.dump(v1_cache_data, f)

    migration = CacheMigration(backup=True, backup_suffix=".bak")
    stats = migration.migrate_directory(temp_cache_dir, dry_run=False)

    assert stats["migrated"] == 2

    # Verify backups exist
    for i in range(2):
        backup_file = temp_cache_dir / f"cache_{i}.json.bak"
        assert backup_file.exists()


# Integration Tests


def test_full_migration_workflow(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test complete migration workflow from v0.0 to v0.1."""
    # Create v0.0 cache
    cache_file = temp_cache_dir / "workflow_test.json"
    with cache_file.open("w") as f:
        json.dump(v1_cache_data, f)

    # Perform migration with backup
    migration = CacheMigration(backup=True)
    success, message = migration.migrate_file(cache_file, dry_run=False)

    assert success is True

    # Verify v0.1 structure
    with cache_file.open("r") as f:
        data = json.load(f)

    assert data["metadata"]["version"] == "0.1"
    assert data["metadata"]["execution_attempts"] == 0
    assert data["metadata"]["is_valid"] is True
    assert len(data["trajectory"]) == 2
    assert data["placeholders"] == {}

    # Verify backup
    backup_file = cache_file.with_suffix(cache_file.suffix + ".v1.backup")
    assert backup_file.exists()

    # Attempt to migrate again (should skip)
    success, message = migration.migrate_file(cache_file, dry_run=False)
    assert success is False
    assert "Already v0.1" in message


def test_migration_preserves_trajectory_data(
    temp_cache_dir: Path, v1_cache_data: list[dict[str, Any]]
) -> None:
    """Test that migration preserves all trajectory data."""
    cache_file = temp_cache_dir / "preserve_test.json"
    with cache_file.open("w") as f:
        json.dump(v1_cache_data, f)

    migration = CacheMigration()
    migration.migrate_file(cache_file, dry_run=False)

    # Load migrated file
    with cache_file.open("r") as f:
        data = json.load(f)

    # Verify trajectory preserved
    assert len(data["trajectory"]) == len(v1_cache_data)
    for i, step in enumerate(data["trajectory"]):
        assert step["id"] == v1_cache_data[i]["id"]
        assert step["name"] == v1_cache_data[i]["name"]
        assert step["input"] == v1_cache_data[i]["input"]
