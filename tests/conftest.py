from redis import asyncio as aioredis
from async_asgi_testclient import TestClient
from chat.api import app
from httpx import AsyncClient
import pytest_asyncio
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
import json
from datetime import datetime, timezone

load_dotenv()


class Settings(BaseSettings):
    redis_test_url: str = Field(env="REDIS_TEST_URL")


settings = Settings()


@pytest_asyncio.fixture
async def redis(monkeypatch):
    redis = aioredis.from_url(settings.redis_test_url, decode_responses=True)
    monkeypatch.setattr("chat.db.redis", redis)
    yield redis
    await redis.flushdb()
    await redis.close()


@pytest_asyncio.fixture
async def websocket_redis(monkeypatch):
    redis = aioredis.from_url(settings.redis_test_url, decode_responses=True)
    monkeypatch.setattr("chat.api.redis", redis)
    yield redis
    await redis.flushdb()
    await redis.close()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def websocket_client():
    async with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def test_data(redis):
    chat_data = {
        "chat_id": "CHT:test_id",
        "name": "Test Chat",
        "ts": "2024-11-11T13:36:40",
    }
    messages = [
        {
            "chat_id": "CHT:test_id",
            "message_id": "MSG:test_id_1",
            "text": "hi, its test 1!",
            "ts": "2024-11-11T13:37:40",
        },
        {
            "chat_id": "CHT:test_id",
            "message_id": "MSG:test_id_2",
            "text": "hello again, test 2!",
            "ts": "2024-11-11T13:39:00",
        },
    ]
    async with redis.pipeline(transaction=True) as pipe:
        await pipe.hset(f'chat:{chat_data["chat_id"]}', mapping=chat_data)
        for message in messages:
            ts = message["ts"]
            timestamp_score = (
                datetime.fromisoformat(ts)
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
            await pipe.hset(
                f'chat:{message["chat_id"]}:message',
                message["message_id"],
                json.dumps(message),
            )
            await pipe.zadd(
                f'chat:{message["chat_id"]}:messages:ts',
                {message["message_id"]: timestamp_score},
            )
        await pipe.execute()

    yield
    await redis.delete(
        'chat:{chat_data["chat_id"]}',
        *(f'chat:{message["chat_id"]}:message' for message in messages),
        f'chat:{messages[0]["chat_id"]}:messages:ts',
    )
