import pytest
import aioredis
from chat.main import app
from httpx import AsyncClient
import pytest_asyncio
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='APP_')
    redis_url: str = Field(env="REDIS_TEST_URL")

settings = Settings()


@pytest_asyncio.fixture
async def redis():
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    yield redis
    await redis.flushdb()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def test_data(redis):
    megadata = {
            "chat_id": "CHT:test_id",
            "message_id": "MSG:test_id",
            "text": "hi, its test!",
            "ts": "2024-11-11T13:36:25",
        }
    await redis.hset(
        f'chat:{megadata["chat_id"]}:message:{megadata["message_id"]}', 
        mapping=megadata
    )
    yield
    await redis.delete(f'chat:{megadata["chat_id"]}:message:{megadata["message_id"]}')