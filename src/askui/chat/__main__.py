import uvicorn

from askui.chat.api.app import app
from askui.chat.api.dependencies import get_settings
from askui.chat.api.telemetry.integrations.fastapi import instrument
from askui.telemetry.otel import setup_opentelemetry_tracing

if __name__ == "__main__":
    settings = get_settings()
    instrument(app, settings.telemetry)
    if settings.otel.enabled:
        setup_opentelemetry_tracing(app, settings.otel)

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,
        workers=1,
        log_config=None,
    )
