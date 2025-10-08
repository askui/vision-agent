import uvicorn
from askui.chat.api.app import app
from askui.chat.api.dependencies import get_settings
from askui.chat.api.telemetry.integrations.fastapi import instrument
from askui.chat.migrations import MigrationRunner

if __name__ == "__main__":
    settings = get_settings()

    # Run migration if needed
    runner = MigrationRunner(settings.db.url)
    if runner.should_migrate(settings.data_dir):
        print("Starting database migration...")
        runner.migrate(settings.data_dir)
        print("Migration completed")

    instrument(app, settings.telemetry)
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,
        workers=1,
        log_config=None,
    )
