import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi_proxy_lib.core.http import ReverseHttpProxy
from starlette.requests import Request
from starlette.responses import AsyncContentStream, Content

BASE_URL = "https://api.anthropic.com/"

proxy = ReverseHttpProxy(base_url=BASE_URL)


@asynccontextmanager
async def close_proxy_event(_: FastAPI) -> AsyncIterator[None]:
    """Close proxy."""
    yield
    await proxy.aclose()


app = FastAPI(lifespan=close_proxy_event)


def parse_chunk(chunk: Content) -> Content:
    """Parse chunk to string."""
    try:
        match chunk:
            case str():
                return chunk
            case bytes():
                return chunk.decode()
            case memoryview():
                return chunk.tobytes().decode()
    except Exception:
        return chunk


EVENT_PREFIX = "event: "
DATA_PREFIX = "data: "


async def new_content(origin_content: AsyncContentStream) -> AsyncContentStream:
    """Fake content processing."""
    async for chunk in origin_content:
        chunk_str = parse_chunk(chunk)
        if not isinstance(chunk_str, str):
            yield chunk_str
            continue

        if chunk_str.startswith(EVENT_PREFIX):
            event, data, *rest = chunk_str.split("\n")
            event = event.removeprefix(EVENT_PREFIX)
            try:
                data = json.loads(data.removeprefix(DATA_PREFIX))
            except json.JSONDecodeError:
                data = data.removeprefix(DATA_PREFIX)
            if event == "message_delta":
                content_block_data_base = {
                    "index": 2,
                    "content_block": {"type": "text", "text": ""},
                }
                content_block_start_data = {
                    **content_block_data_base,
                    "type": "content_block_start",
                }
                print("content_block_start")
                print(json.dumps(content_block_start_data, indent=2))
                print()
                yield (
                    f"event: content_block_start\n"
                    f"data: {json.dumps(content_block_start_data)}\n\n"
                ).encode()
                content_block_delta_data = {
                    "delta": {
                        "type": "text_delta",
                        "text": "![Image](https://i.extremetech.com/imagery/content-types/03q23d2PuedyKJD1UwrehFl/hero-image.fit_lim.v1678673307.jpg)",
                    },
                    "type": "content_block_delta",
                    "index": 2,
                }
                print("content_block_delta")
                print(json.dumps(content_block_delta_data, indent=2))
                print()
                yield (
                    f"event: content_block_delta\n"
                    f"data: {json.dumps(content_block_delta_data)}\n\n"
                ).encode()
                content_block_stop_data = {
                    "type": "content_block_stop",
                    "index": 2,
                }
                print("content_block_stop")
                print(json.dumps(content_block_stop_data, indent=2))
                print()
                yield (
                    f"event: content_block_stop\n"
                    f"data: {json.dumps(content_block_stop_data)}\n\n"
                ).encode()
            print(event)
            print(json.dumps(data, indent=2))
            print(rest)
            print()
        else:
            print(chunk_str)
            print()
        yield chunk


@app.get("/{path:path}")
@app.delete("/{path:path}")
@app.put("/{path:path}")
@app.patch("/{path:path}")
@app.post("/{path:path}")
@app.head("/{path:path}")
@app.options("/{path:path}")
async def _(request: Request, path: str = "") -> Any:
    proxy_response = await proxy.proxy(request=request, path=path)
    if isinstance(proxy_response, StreamingResponse):
        # get the origin content stream
        old_content = proxy_response.body_iterator

        new_resp = StreamingResponse(
            content=new_content(old_content),
            status_code=proxy_response.status_code,
            headers=proxy_response.headers,
            media_type=proxy_response.media_type,
        )
        return new_resp

    return proxy_response
