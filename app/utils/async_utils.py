"""Async utilities for running blocking operations with timeouts."""

import asyncio
from typing import Any, Callable

from app.utils.config import get_settings


async def run_with_timeout(func: Callable[..., Any], *args: Any) -> Any:
    """Run a synchronous function in a thread pool with a timeout.

    Args:
        func: A synchronous callable to execute.
        *args: Arguments to pass to the callable.

    Returns:
        The result of the callable.

    Raises:
        asyncio.TimeoutError: If execution exceeds the configured timeout.
    """
    timeout = get_settings().request_timeout
    return await asyncio.wait_for(asyncio.to_thread(func, *args), timeout=timeout)
