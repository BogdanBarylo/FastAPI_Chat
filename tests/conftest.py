import pytest
import aioredis
from chat.main import app
from fastapi.testclient import TestClient

@pytest.fixture()
async def redis_test_connect():
    redis = aioredis.from_url("redis://localhost:6379/1", decode_responses=True)
    yield redis
    await redis.flushdb()

@pytest.fixture()
def get_client():
    client = TestClient(app)
    return client