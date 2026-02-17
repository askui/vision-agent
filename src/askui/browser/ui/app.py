import base64
import io
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import aiofiles
import anyio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from askui.web_agent import WebVisionAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global agent instance
agent: Optional[WebVisionAgent] = None


class Instruction(BaseModel):
    text: str


class MouseEvent(BaseModel):
    x: int
    y: int
    button: str = "left"
    repeat: int = 1


class KeyboardEvent(BaseModel):
    key: str
    type: str  # "type", "down", "up"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    global agent
    logger.info("Starting up browser agent...")
    # Using headless=True so we can stream screenshots to the UI
    agent = WebVisionAgent(headless=True)
    await anyio.to_thread.run_sync(agent.__enter__)
    yield
    if agent:
        logger.info("Shutting down browser agent...")
        await anyio.to_thread.run_sync(agent.__exit__, None, None, None)


app = FastAPI(title="AskUI Autonomous Browser UI", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def get_index() -> str:
    index_path = Path(__file__).parent / "index.html"
    async with aiofiles.open(index_path, "r") as f:
        return await f.read()


@app.post("/act")
async def act(instruction: Instruction) -> dict[str, str]:
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        logger.info("Executing: %s", instruction.text)
        await anyio.to_thread.run_sync(agent.act, instruction.text)
    except Exception as e:  # noqa: BLE001
        logger.exception("Error executing instruction")
        return {"status": "error", "message": str(e)}
    else:
        return {"status": "success"}


@app.get("/screenshot")
async def get_screenshot() -> dict[str, str]:
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        img = await anyio.to_thread.run_sync(agent.tools.os.screenshot)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        logger.exception("Error taking screenshot")
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        return {"screenshot": img_str}


@app.post("/mouse/click")
async def mouse_click(event: MouseEvent) -> dict[str, str]:
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        await anyio.to_thread.run_sync(agent.tools.os.mouse_move, event.x, event.y)
        button = event.button if event.button in ["left", "middle", "right"] else "left"
        await anyio.to_thread.run_sync(
            agent.tools.os.click,
            button,
            event.repeat,  # type: ignore[arg-type]
        )
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "message": str(e)}
    else:
        return {"status": "success"}


@app.post("/keyboard/type")
async def keyboard_type(event: KeyboardEvent) -> dict[str, str]:
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        if event.type == "type":
            await anyio.to_thread.run_sync(agent.tools.os.type, event.key)
        elif event.type == "down":
            await anyio.to_thread.run_sync(
                agent.tools.os.keyboard_pressed,
                event.key,  # type: ignore[arg-type]
            )
        elif event.type == "up":
            await anyio.to_thread.run_sync(
                agent.tools.os.keyboard_release,
                event.key,  # type: ignore[arg-type]
            )
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "message": str(e)}
    else:
        return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
