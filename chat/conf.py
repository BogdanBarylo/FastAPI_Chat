from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from redis import asyncio as aioredis

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")
    redis_url: str = Field(env="REDIS_URL")
    redis_test_url: str = Field(env="REDIS_TEST_URL")

settings = Settings()
redis = aioredis.from_url(settings.redis_url, decode_responses=True)
