import uvicorn

from askui.chat.api.app import app
from askui.chat.api.dependencies import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=False,
        workers=1,
    )
