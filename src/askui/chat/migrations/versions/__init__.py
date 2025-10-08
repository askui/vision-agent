"""Migration versions registry."""

from . import migration_001_initial_schema, migration_002_migrate_json_to_sqlite

MIGRATIONS = {
    1: migration_001_initial_schema,
    2: migration_002_migrate_json_to_sqlite,
}
