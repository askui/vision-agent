from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from askui.chat.api.messages.router import router as messages_router
from askui.chat.api.runs.router import router as runs_router
from askui.chat.api.threads.router import router as threads_router

app = FastAPI(
    title="AskUI Chat API",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(threads_router)
v1_router.include_router(messages_router)
v1_router.include_router(runs_router)
app.include_router(v1_router)
