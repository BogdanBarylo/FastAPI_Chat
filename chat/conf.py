from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

load_dotenv()


class Settings(BaseSettings):
    redis_url: str = Field(env="REDIS_URL")


settings = Settings()
