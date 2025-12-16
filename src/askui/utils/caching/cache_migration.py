"""Cache migration utilities for converting v0.0 caches to v0.1 format.

This module provides tools to batch migrate existing v0.0 cache files to the new
v0.1 format with metadata support. Individual files are automatically migrated on
first read by CacheWriter, but this utility is useful for:

1. Batch migration of all caches in a directory
2. Pre-migration without executing caches
3. Verification of migration success
4. Backup creation before migration

Usage:
    # Migrate all caches in a directory
    python -m askui.utils.cache_migration --cache-dir .cache

    # Dry run (don't modify files)
    python -m askui.utils.cache_migration --cache-dir .cache --dry-run

    # Create backups before migration
    python -m askui.utils.cache_migration --cache-dir .cache --backup
"""

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from askui.utils.caching.cache_writer import CacheWriter

logger = logging.getLogger(__name__)


class CacheMigrationError(Exception):
    """Raised when cache migration fails."""


class CacheMigration:
    """Handles migration of cache files from v0.0 to v0.1 format."""

    def __init__(
        self,
        backup: bool = False,
        backup_suffix: str = ".v1.backup",
    ):
        """Initialize cache migration utility.

        Args:
            backup: Whether to create backup files before migration
            backup_suffix: Suffix to add to backup files
        """
        self.backup = backup
        self.backup_suffix = backup_suffix
        self.migrated_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def migrate_file(self, file_path: Path, dry_run: bool = False) -> tuple[bool, str]:
        """Migrate a single cache file from v0.0 to v0.1.

        Args:
            file_path: Path to the cache file
            dry_run: If True, don't modify the file

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not file_path.is_file():
            return False, f"File not found: {file_path}"

        try:
            # Read the file
            with file_path.open("r") as f:
                data = json.load(f)

            # Check if already v0.1
            if isinstance(data, dict) and "metadata" in data:
                version = data.get("metadata", {}).get("version")
                if version == "0.1":
                    return False, f"Already v0.1: {file_path.name}"

            # Use CacheWriter to read (automatically migrates)
            try:
                cache_file = CacheWriter.read_cache_file(file_path)
            except Exception as e:  # noqa: BLE001
                return False, f"Failed to read cache: {str(e)}"

            # Verify it's now v0.1
            if cache_file.metadata.version != "0.1":
                return (
                    False,
                    f"Migration failed: Version is {cache_file.metadata.version}",
                )

            if dry_run:
                return True, f"Would migrate: {file_path.name}"

            # Create backup if requested
            if self.backup:
                backup_path = file_path.with_suffix(
                    file_path.suffix + self.backup_suffix
                )
                shutil.copy2(file_path, backup_path)
                logger.debug("Created backup: %s", backup_path)

            # Write migrated version back
            with file_path.open("w") as f:
                json.dump(cache_file.model_dump(mode="json"), f, indent=2, default=str)

        except Exception as e:  # noqa: BLE001
            logger.exception("Error migrating %s", file_path)
            return False, f"Error: {str(e)}"
        else:
            return True, f"Migrated: {file_path.name}"

    def migrate_directory(
        self,
        cache_dir: Path,
        file_pattern: str = "*.json",
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Migrate all cache files in a directory.

        Args:
            cache_dir: Directory containing cache files
            file_pattern: Glob pattern for cache files
            dry_run: If True, don't modify files

        Returns:
            Dictionary with migration statistics
        """
        if not cache_dir.is_dir():
            msg = f"Directory not found: {cache_dir}"
            raise CacheMigrationError(msg)

        # Find all cache files
        cache_files = list(cache_dir.glob(file_pattern))

        if not cache_files:
            logger.warning("No cache files found in %s", cache_dir)
            return {
                "migrated": 0,
                "skipped": 0,
                "errors": 0,
                "total": 0,
            }

        logger.info("Found %s cache files in %s", len(cache_files), cache_dir)

        # Reset counters
        self.migrated_count = 0
        self.skipped_count = 0
        self.error_count = 0

        # Migrate each file
        results = []
        for file_path in cache_files:
            success, message = self.migrate_file(file_path, dry_run=dry_run)

            if success:
                self.migrated_count += 1
                logger.info("✓ %s", message)
            elif "Already v0.1" in message:
                self.skipped_count += 1
                logger.debug("⊘ %s", message)
            else:
                self.error_count += 1
                logger.error("✗ %s", message)

            results.append(
                {"file": file_path.name, "success": success, "message": message}
            )

        # Log summary
        logger.info("\n%s", "=" * 60)
        logger.info("Migration Summary:")
        logger.info("  Total files:    %s", len(cache_files))
        logger.info("  Migrated:       %s", self.migrated_count)
        logger.info("  Already v0.1:   %s", self.skipped_count)
        logger.info("  Errors:         %s", self.error_count)
        logger.info("%s\n", "=" * 60)

        return {
            "migrated": self.migrated_count,
            "skipped": self.skipped_count,
            "errors": self.error_count,
            "total": len(cache_files),
            "results": results,
        }


def main() -> int:
    """CLI entry point for cache migration.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Migrate cache files from v0.0 to v0.1 format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate all caches in .cache directory
  python -m askui.utils.cache_migration --cache-dir .cache

  # Dry run (show what would be migrated)
  python -m askui.utils.cache_migration --cache-dir .cache --dry-run

  # Create backups before migration
  python -m askui.utils.cache_migration --cache-dir .cache --backup

  # Custom file pattern
  python -m askui.utils.cache_migration --cache-dir .cache --pattern "test_*.json"
        """,
    )

    parser.add_argument(
        "--cache-dir",
        type=str,
        required=True,
        help="Directory containing cache files to migrate",
    )

    parser.add_argument(
        "--pattern",
        type=str,
        default="*.json",
        help="Glob pattern for cache files (default: *.json)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without modifying files",
    )

    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup files before migration (adds .v1.backup suffix)",
    )

    parser.add_argument(
        "--backup-suffix",
        type=str,
        default=".v1.backup",
        help="Suffix for backup files (default: .v1.backup)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        cache_dir = Path(args.cache_dir)

        if args.dry_run:
            logger.info("DRY RUN MODE - No files will be modified\n")

        # Create migration utility
        migration = CacheMigration(
            backup=args.backup,
            backup_suffix=args.backup_suffix,
        )

        # Perform migration
        stats = migration.migrate_directory(
            cache_dir=cache_dir,
            file_pattern=args.pattern,
            dry_run=args.dry_run,
        )

        # Return success if no errors
        if stats["errors"] == 0:
            logger.info("✓ Migration completed successfully!")
        else:
            logger.error("✗ Migration completed with %s errors", stats["errors"])
            return 1

    except CacheMigrationError:
        logger.exception("Migration failed")
        return 1
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user")
        return 1
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error")
        return 1
    else:
        return 0


if __name__ == "__main__":
    exit(main())
