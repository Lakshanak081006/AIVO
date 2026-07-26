from __future__ import annotations
import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar
from app.core.config import settings
T=TypeVar("T")

async def with_retry(operation: Callable[[], Awaitable[T]], *, attempts: int | None=None, on_retry=None) -> T:
    maximum=settings.MAX_TOOL_RETRIES if attempts is None else attempts
    last_error: Exception | None=None
    for retry in range(maximum+1):
        try:
            return await operation()
        except Exception as exc:
            last_error=exc
            if retry>=maximum: break
            delay=settings.RETRY_BASE_DELAY_SECONDS*(2**retry)
            if on_retry: on_retry(retry+1, delay, exc)
            await asyncio.sleep(delay)
    assert last_error is not None
    raise last_error
