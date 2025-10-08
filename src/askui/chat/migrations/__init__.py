"""Migration framework for chat API."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from askui.chat.api.db.base import Base
from askui.chat.api.migrations.models import MigrationVersionModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class MigrationRunner:
    """Handles database migrations for chat API.

    Uses version-based migrations stored in the database rather than
    external migration files like Alembic.
    """

    def __init__(self, database_url: str) -> None:
        """Initialize migration runner.

        Args:
            database_url (str): Database URL for SQLAlchemy connection.
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)

    def get_current_version(self) -> int:
        """Get current schema version from database.

        Returns:
            int: Current schema version, or 0 if no version found.
        """
        with self.engine.connect() as conn:
            try:
                result = conn.execute(
                    text("SELECT MAX(version) FROM migration_version")
                )
                version = result.scalar()
                return version if version else 0
            except Exception:
                return 0

    def should_migrate(self, data_dir: Path) -> bool:
        """Check if migration is needed.

        Args:
            data_dir (Path): Directory containing JSON/JSONL files.

        Returns:
            bool: True if migration is needed.
        """
        current_version = self.get_current_version()

        # Import migrations here to avoid circular imports
        from .versions import MIGRATIONS

        target_version = max(MIGRATIONS.keys())

        # Need to migrate if version is behind
        if current_version < target_version:
            return True

        # Also check if JSON files exist (for initial migration)
        if current_version == 0:
            json_dirs = [
                "assistants",
                "threads",
                "messages",
                "runs",
                "files",
                "mcp_configs",
                "workflows",
            ]
            for dir_name in json_dirs:
                dir_path = data_dir / dir_name
                if dir_path.exists():
                    json_files = list(dir_path.glob("*.json"))
                    if json_files:
                        return True

        return False

    def migrate(self, data_dir: Path) -> None:
        """Run all pending migrations.

        Args:
            data_dir (Path): Directory containing JSON/JSONL files.
        """
        current_version = self.get_current_version()

        # Import migrations here to avoid circular imports
        from .versions import MIGRATIONS

        target_version = max(MIGRATIONS.keys())

        for version in range(current_version + 1, target_version + 1):
            if version in MIGRATIONS:
                migration = MIGRATIONS[version]
                print(f"Running migration {version}: {migration.__name__}")
                migration.upgrade(self.engine, data_dir)

                # Record version
                with self.engine.begin() as conn:
                    conn.execute(
                        text(
                            "INSERT INTO migration_version (version, applied_at) VALUES (:v, :t)"
                        ),
                        {"v": version, "t": datetime.now(timezone.utc)},
                    )

        print("Migration completed successfully")


# Migration functions registry
MIGRATIONS: dict[int, Callable] = {}


def register_migration(version: int) -> Callable:
    """Decorator to register a migration function.

    Args:
        version (int): Migration version number.

    Returns:
        Callable: Decorator function.
    """

    def decorator(func: Callable) -> Callable:
        MIGRATIONS[version] = func
        return func

    return decorator
