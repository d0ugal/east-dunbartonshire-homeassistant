"""Shared fixtures for integration tests."""

import aiohttp
import pytest_asyncio


@pytest_asyncio.fixture
async def session():
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        yield s
