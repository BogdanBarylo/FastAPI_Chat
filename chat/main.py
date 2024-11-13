from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime, timezone
from redis import asyncio as aioredis
from dotenv import load_dotenv
from sqids import Sqids
import json


load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='APP_')
    redis_url: str = Field(env="REDIS_URL")


settings = Settings()
redis = aioredis.from_url(settings.redis_url, decode_responses=True)
app = FastAPI()


def get_id(number):
    sqids = Sqids()
    return sqids.encode([number])


def get_format_time(ts):
    formatted_ts = ts.strftime("%Y-%m-%dT%H:%M:%S")
    return formatted_ts


class CreateChatRequest(BaseModel):
    name: str = Field(
        min_length=1, max_length=120, description="Name of the chat"
    )


class CreateChatResponse(BaseModel):
    chat_id: str = Field(description="Id of the chat")
    name: str = Field(
        min_length=1, max_length=120, description="Name of the chat"
    )
    url: str = Field(description="Url of the chat")
    ts: datetime = Field(description="Create time")


@app.post("/chats")
async def create_chat(chat: CreateChatRequest) -> CreateChatResponse:
    chat_number = await redis.incr("chat_id_counter")
    chat_id = f"CHT:{get_id(chat_number)}"
    ts = datetime.now(timezone.utc)
    formated_ts = get_format_time(ts)
    url = f"/chats/{chat_id}"
    await redis.hset(
        f"chat:{chat_id}",
        mapping={
            "chat_id": chat_id,
            "name": chat.name,
            "ts": formated_ts,
        },
    )
    chat_response = CreateChatResponse(
        chat_id=chat_id, name=chat.name, url=url, ts=formated_ts
    )
    return chat_response


class CreateMessageRequest(BaseModel):
    text: str = Field(
        min_length=1, max_length=500, description="Text of the message"
    )


class CreateMessageResponse(BaseModel):
    chat_id: str = Field(description="Id of the chat")
    message_id: str = Field(description="Id of the message")
    text: str = Field(
        min_length=1, max_length=500, description="Text of the message"
    )
    ts: datetime = Field(description="Create time")


@app.post("/chats/{chat_id}/messages")
async def create_message(
    chat_id: str, message: CreateMessageRequest
) -> CreateMessageResponse:
    message_number = await redis.incr("message_id_counter")
    message_id = f"MSG:{get_id(message_number)}"
    ts = datetime.now(timezone.utc)
    formated_ts = get_format_time(ts)
    message_data = json.dumps(
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": message.text,
            "ts": formated_ts,
        }
    )
    timestamp_score = ts.timestamp()
    async with redis.pipeline(transaction=True) as pipe:
        await redis.hset(f"chat:{chat_id}:message", message_id, message_data)
        await redis.zadd(
            f"chat:{chat_id}:messages:ts", {message_id: timestamp_score}
        )
        await pipe.execute()
    new_message = CreateMessageResponse(
        chat_id=chat_id, message_id=message_id, text=message.text, ts=formated_ts
    )
    return new_message


class GetMessagesResponse(BaseModel):
    messages: list[CreateMessageResponse] = Field(
        description="All founded messages in this chat"
    )


GetMessagesTsParam = Query(
    default=None,
    description="The time by which you want to receive messages")

GetMessagesLimitParam = Query(
    default=10,
    description="Maximum number of returned messages")


@app.get("/chats/{chat_id}/messages")
async def get_messages(
    chat_id: str,
    ts_message: datetime | None = GetMessagesTsParam,
    limit: int = GetMessagesLimitParam,
) -> GetMessagesResponse:
    chat_exists = await redis.exists(f"chat:{chat_id}")
    if not chat_exists:
        raise HTTPException(
            status_code=404,
            detail="Chat does not exist, please check if the id is correct")
    messages = []
    if ts_message:
        date_filter = ts_message.replace(tzinfo=timezone.utc).timestamp()
    else:
        date_filter = "+inf"
    message_ids = await redis.zrangebyscore(
        f"chat:{chat_id}:messages:ts", "-inf", date_filter, start=0, num=limit
    )
    messages = []
    async with redis.pipeline() as pipe:
        for message_id in message_ids:
            pipe.hget(f"chat:{chat_id}:message", message_id)
        message_data_list = await pipe.execute()
    for message_data in message_data_list:
        if message_data:
            message_obj = CreateMessageResponse.model_validate_json(message_data)
            messages.append(message_obj)
    return GetMessagesResponse(messages=messages)


@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    chat_data = await redis.hgetall(f"chat:{chat_id}")
    if not chat_data:
        raise HTTPException(
            status_code=404,
            detail="Chat does not exist, please check if the id is correct",
        )
    message_ids = await redis.zrange(f"chat:{chat_id}:messages:ts", 0, -1)
    async with redis.pipeline(transaction=True) as pipe:
        for message_id in message_ids:
            await redis.delete(f"chat:{chat_id}:message:{message_id}")
        await redis.delete(f"chat:{chat_id}:messages:ts")
        await redis.delete(f"chat:{chat_id}")
        await pipe.execute()
