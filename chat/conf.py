from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")
    redis_url: str = Field(env="REDIS_URL")


settings = Settings()
