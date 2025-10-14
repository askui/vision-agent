# Database Migrations

This document explains how database migrations work in the AskUI Chat system.

## Overview

Database migrations are used to manage changes to the database schema and data over time. They ensure that your database structure stays in sync with the application code and handle data transformations when the schema changes.

## What Are Migrations Used For?

Migrations in the AskUI Chat system are primarily used for:

- **Schema Changes**: Creating, modifying, or dropping database tables and columns
- **Data Migrations**: Transforming existing data when the schema changes
- **Persistence Layer Evolution**: Migrating from one persistence format to another (e.g., JSON files to SQLite database)
- **Seed Data**: Populating the database with default data

### Example Use Cases

The current migration history shows several real-world examples:

1. **`4d1e043b4254_create_assistants_table.py`**: Creates the initial `assistants` table with columns for ID, workspace, timestamps, and assistant configuration
2. **`057f82313448_import_json_assistants.py`**: Migrates existing assistant data from JSON files to the new SQLite database
3. **`c35e88ea9595_seed_default_assistants.py`**: Seeds the database with default assistant configurations
4. **`37007a499ca7_remove_assistants_dir.py`**: Cleans up the old JSON-based persistence by removing the assistants directory

## Automatic Migrations on Startup

By default, migrations are automatically run when the chat API starts up. This ensures that users are always upgraded to the newest database schema version without manual intervention.

### Configuration

The automatic migration behavior is controlled by the `auto_migrate` setting in the database configuration:

```python
class DbSettings(BaseModel):
    auto_migrate: bool = Field(
        default=True,
        description="Whether to run migrations automatically on startup",
    )
```

### Environment Variable Override

You can disable automatic migrations for debugging purposes using the environment variable:

```bash
export ASKUI__CHAT_API__DB__AUTO_MIGRATE=false
```

When disabled, the application will log:
```
Automatic migrations are disabled. Skipping migrations...
```

## Manual Migration Commands

You can run migrations manually using the Alembic command-line interface:

```bash
# Run all pending migrations
pdm run alembic upgrade head

# Run migrations to a specific revision
pdm run alembic upgrade <revision_id>

# Downgrade to a previous revision
pdm run alembic downgrade <revision_id>

# Show current migration status
pdm run alembic current

# Show migration history
pdm run alembic history

# Generate a new migration
pdm run alembic revision --autogenerate -m "description of changes"
```

## Migration Structure

### Directory Layout

```
src/askui/chat/migrations/
├── alembic.ini          # Alembic configuration
├── env.py              # Migration environment setup
├── runner.py           # Migration runner for programmatic execution
├── script.py.mako      # Template for new migration files
├── shared/             # Shared utilities and models for migrations
│   ├── assistants/     # Assistant-related migration utilities
│   ├── models.py       # Shared data models
│   └── settings.py     # Settings for migrations
└── versions/           # Individual migration files
    ├── 4d1e043b4254_create_assistants_table.py
    ├── 057f82313448_import_json_assistants.py
    ├── c35e88ea9595_seed_default_assistants.py
    └── 37007a499ca7_remove_assistants_dir.py
```

### Migration File Structure

Each migration file follows this structure:

```python
"""migration_description

Revision ID: <revision_id>
Revises: <previous_revision_id>
Create Date: <timestamp>

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "<revision_id>"
down_revision: Union[str, None] = "<previous_revision_id>"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the migration changes."""
    # Migration logic here
    pass


def downgrade() -> None:
    """Revert the migration changes."""
    # Rollback logic here
    pass
```

## Migration Execution Flow

1. **Startup Check**: When the chat API starts, it checks the `auto_migrate` setting
2. **Migration Runner**: If enabled, calls `run_migrations()` from `runner.py`
3. **Alembic Execution**: Uses Alembic's `upgrade` command to apply all pending migrations
4. **Database Connection**: Connects to the database using settings from `env.py`
5. **Schema Application**: Applies each migration in sequence until reaching the "head" revision

## Database Configuration

The migration system uses the same database configuration as the main application:

- **Database URL**: Configured via `ASKUI__CHAT_API__DB__URL` (defaults to SQLite)
- **Connection**: Uses the same SQLAlchemy engine as the main application
- **Metadata**: Automatically detects schema changes from SQLAlchemy models

## Best Practices

### Creating New Migrations

1. **Use Autogenerate**: Let Alembic detect schema changes automatically:
   ```bash
   pdm run alembic revision --autogenerate -m "add new column to table"
   ```

2. **Review Generated Code**: Always review and test autogenerated migrations before applying

3. **Handle Data Migrations**: For complex data transformations, write custom migration logic

4. **Test Both Directions**: Ensure both `upgrade()` and `downgrade()` functions work correctly

### Migration Safety

1. **Backup First**: Always backup database before running migrations so that it can be easily rolled back if something goes wrong
2. **Test Locally**: Test migrations on a copy of production data
3. **Rollback Plan**: Have a rollback strategy for critical migrations
4. **Batch Operations**: For large data migrations, process data in batches to avoid memory issues
5. **Keep Old Code Around**: Keep old code versioned around so that migrations are independent of the version of AskUI chat

## Troubleshooting

### Common Issues

1. **Migration Conflicts**: If multiple developers create migrations simultaneously, you may need to resolve conflicts manually
2. **Data Loss**: Some migrations (like dropping columns) can cause data loss - always review carefully
3. **Performance**: Large data migrations can be slow - consider running them not during startup but in the background maintaining compatibility with old code for as long as it runs or just disabling certain apis for that period of time

### Debugging

1. **Check Migration Status**:
   ```bash
   pdm run alembic current
   ```

2. **View Migration History**:
   ```bash
   pdm run alembic history --verbose
   ```

3. **Disable Auto-Migration**: Use the environment variable to disable automatic migrations during debugging

## Related Documentation

- [Alembic Documentation](https://alembic.sqlalchemy.org/) - Official Alembic migration tool documentation
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/) - SQLAlchemy ORM and database toolkit
- [Database Models](../src/askui/chat/api/) - Current database schema and models
