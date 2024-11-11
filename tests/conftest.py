import pytest
import aioredis
from chat.main import app
from httpx import AsyncClient
import pytest_asyncio


@pytest_asyncio.fixture
async def redis():
    redis = aioredis.from_url(
        "redis://localhost:6379/1", decode_responses=True
    )
    yield redis
    await redis.flushdb()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def test_data(redis):
    megadata = {}
    redis.insert(megadata)
    yield
    redis.delete(megadata)