from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from askui.chat.api.assistants.dependencies import get_assistant_service
from askui.chat.api.assistants.router import router as assistants_router
from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_settings
from askui.chat.api.health.router import router as health_router
from askui.chat.api.messages.router import router as messages_router
from askui.chat.api.runs.router import router as runs_router
from askui.chat.api.threads.router import router as threads_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    assistant_service = get_assistant_service(settings=get_settings())
    assistant_service.seed()
    yield


app = FastAPI(
    title="AskUI Chat API",
    version="0.1.0",
    lifespan=lifespan,
    dependencies=[SetEnvFromHeadersDep],
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
v1_router.include_router(assistants_router)
v1_router.include_router(threads_router)
v1_router.include_router(messages_router)
v1_router.include_router(runs_router)
v1_router.include_router(health_router)
app.include_router(v1_router)
