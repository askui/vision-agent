import base64
import io
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from askui.web_agent import WebVisionAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AskUI Autonomous Browser UI")

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

@app.on_event("startup")
async def startup_event():
    global agent
    logger.info("Starting up browser agent...")
    # Using headless=True so we can stream screenshots to the UI
    agent = WebVisionAgent(headless=True)
    agent.__enter__()

@app.on_event("shutdown")
async def shutdown_event():
    global agent
    if agent:
        logger.info("Shutting down browser agent...")
        agent.__exit__(None, None, None)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("src/askui/browser/ui/index.html", "r") as f:
        return f.read()

@app.post("/act")
async def act(instruction: Instruction):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        logger.info(f"Executing: {instruction.text}")
        agent.act(instruction.text)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error executing instruction: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/screenshot")
async def get_screenshot():
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        img = agent.tools.os.screenshot()
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return {"screenshot": img_str}
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mouse/click")
async def mouse_click(event: MouseEvent):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        agent.tools.os.mouse_move(event.x, event.y)
        agent.tools.os.click(event.button, event.repeat)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/keyboard/type")
async def keyboard_type(event: KeyboardEvent):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        if event.type == "type":
            agent.tools.os.type(event.key)
        elif event.type == "down":
            agent.tools.os.keyboard_pressed(event.key)
        elif event.type == "up":
            agent.tools.os.keyboard_release(event.key)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
