from concurrent.futures import ThreadPoolExecutor
from typing import Coroutine, Optional, TypeVar

import anyio
import sniffio

ResultT = TypeVar("ResultT")


def run_sync(
    coroutine: Coroutine[object, object, ResultT], timeout: Optional[float]
) -> ResultT:
    """Run coroutine using anyio for better compatibility."""

    # Check if we're already in an async context
    try:
        sniffio.current_async_library()
        # We're in an async context
        return _run_in_thread_from_async(coroutine, timeout)
    except sniffio.AsyncLibraryNotFoundError:
        # We're in a sync context - safe to use anyio.run
        if timeout is not None:
            with anyio.fail_after(timeout):
                return anyio.run(lambda: coroutine)
        else:
            return anyio.run(lambda: coroutine)


def _run_in_thread_from_async(
    coroutine: Coroutine[object, object, ResultT], timeout: Optional[float]
) -> ResultT:
    """Run coroutine in a separate thread when called from async context."""

    # Preserve context variables
    ctx = copy_context()

    def run_in_new_thread():
        # Create fresh event loop in this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:

            async def with_timeout():
                if timeout is not None:
                    return await asyncio.wait_for(coroutine, timeout)
                return await coroutine

            return loop.run_until_complete(with_timeout())
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(ctx.run, run_in_new_thread)
        try:
            # Apply timeout at thread level too
            return future.result(timeout=timeout)
        except TimeoutError:
            # Attempt to clean up the thread
            future.cancel()
            raise TimeoutError(f"Coroutine execution exceeded {timeout} seconds")
