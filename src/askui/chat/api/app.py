from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

from askui.chat.api.assistants.dependencies import get_assistant_service
from askui.chat.api.assistants.router import router as assistants_router
from askui.chat.api.dependencies import SetEnvFromHeadersDep, get_settings
from askui.chat.api.files.router import router as files_router
from askui.chat.api.health.router import router as health_router
from askui.chat.api.mcp_clients.dependencies import get_mcp_client_manager_manager
from askui.chat.api.mcp_clients.manager import McpServerConnectionError
from askui.chat.api.mcp_configs.dependencies import get_mcp_config_service
from askui.chat.api.mcp_configs.router import router as mcp_configs_router
from askui.chat.api.mcp_servers.computer import mcp as computer_mcp
from askui.chat.api.mcp_servers.testing import mcp as testing_mcp
from askui.chat.api.mcp_servers.utility import mcp as utility_mcp
from askui.chat.api.messages.router import router as messages_router
from askui.chat.api.runs.router import router as runs_router
from askui.chat.api.threads.router import router as threads_router
from askui.chat.api.workflows.router import router as workflows_router
from askui.utils.api_utils import (
    ConflictError,
    FileTooLargeError,
    ForbiddenError,
    LimitReachedError,
    NotFoundError,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    settings = get_settings()
    assistant_service = get_assistant_service(settings=settings)
    assistant_service.seed()
    mcp_config_service = get_mcp_config_service(settings=settings)
    mcp_config_service.seed()
    yield
    await get_mcp_client_manager_manager(mcp_config_service).disconnect_all(force=True)


app = FastAPI(
    title="AskUI Chat API",
    version="0.1.0",
    lifespan=lifespan,
)


# Include routers
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(assistants_router)
v1_router.include_router(threads_router)
v1_router.include_router(messages_router)
v1_router.include_router(runs_router)
v1_router.include_router(mcp_configs_router)
v1_router.include_router(files_router)
v1_router.include_router(workflows_router)
v1_router.include_router(health_router)
app.include_router(v1_router)


mcp = FastMCP.from_fastapi(app=app, name="AskUI Chat MCP")
mcp.mount(computer_mcp)
mcp.mount(testing_mcp)
mcp.mount(utility_mcp)
mcp_app = mcp.http_app("/sse", transport="sse")


@asynccontextmanager
async def combined_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with lifespan(app):
        async with mcp_app.lifespan(app):
            yield


app = FastAPI(
    title=app.title,
    version=app.version,
    lifespan=combined_lifespan,
    dependencies=[SetEnvFromHeadersDep],
)
app.mount("/mcp", mcp_app)
app.include_router(v1_router)


@app.exception_handler(NotFoundError)
def not_found_error_handler(
    request: Request,  # noqa: ARG001
    exc: NotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


@app.exception_handler(ConflictError)
def conflict_error_handler(
    request: Request,  # noqa: ARG001
    exc: ConflictError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)}
    )


@app.exception_handler(LimitReachedError)
def limit_reached_error_handler(
    request: Request,  # noqa: ARG001
    exc: LimitReachedError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
    )


@app.exception_handler(FileTooLargeError)
def file_too_large_error_handler(
    request: Request,  # noqa: ARG001
    exc: FileTooLargeError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={"detail": str(exc)},
    )


@app.exception_handler(ForbiddenError)
def forbidden_error_handler(
    request: Request,  # noqa: ARG001
    exc: ForbiddenError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
def catch_all_exception_handler(
    request: Request,  # noqa: ARG001
    exc: Exception,
) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(McpServerConnectionError)
def mcp_server_connection_error_handler(
    request: Request,  # noqa: ARG001
    exc: McpServerConnectionError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
