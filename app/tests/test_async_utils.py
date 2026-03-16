import asyncio
import os
import time

import pytest

from app.utils.async_utils import run_with_timeout
from app.utils.config import get_settings


@pytest.mark.asyncio
async def test_run_with_timeout() -> None:
    os.environ["DBP_REQUEST_TIMEOUT"] = "1"
    get_settings.cache_clear()
    with pytest.raises(asyncio.TimeoutError):
        await run_with_timeout(time.sleep, 2)


@pytest.mark.asyncio
async def test_run_with_timeout_success() -> None:
    os.environ["DBP_REQUEST_TIMEOUT"] = "2"
    get_settings.cache_clear()
    await run_with_timeout(time.sleep, 0.1)
