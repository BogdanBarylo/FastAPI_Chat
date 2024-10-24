from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import aioredis
from sqids import Sqids

app = FastAPI()
redis = aioredis.from_url("redis://localhost:6379", decode_responses=True)


class CreateChatRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30,
                      description="Name of the chat")


class CreateChatResponse(BaseModel):
    id: str = Field(..., description="Id of the chat")
    name: str = Field(..., min_length=1, max_length=30,
                      description="Name of the chat")
    url: str = Field(...,  description="Url of the chat")
    ts: str = Field(...,  description="Create time")


@app.post("/chats")
async def create_chat(chat: CreateChatRequest) -> CreateChatResponse:
    chat_number = await redis.incr('chat_id_counter')
    sqids = Sqids()
    id = sqids.encode([chat_number])
    chat_id = f"CHT:{id}"
    chat_ts = datetime.now(timezone.utc).isoformat()
    chat_url = f'/chats/{chat_id}'
    chat_response = CreateChatResponse(id=chat_id,
                                       name=chat.name,
                                       url=chat_url,
                                       ts=chat_ts)
    await redis.hset(f'chat:{chat_id}', mapping={"id": chat_id,
                                                 "name": chat.name,
                                                 "url": chat_url,
                                                 "ts": chat_ts})
    return chat_response


class CreateMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500,
                      description="Text of the message")


class CreateMessageResponse(BaseModel):
    chat_id: str = Field(..., description="Id of the chat")
    id: str = Field(..., description="Id of the message")
    text: str = Field(..., min_length=1, max_length=500,
                      description="Text of the message")
    ts: str = Field(...,  description="Create time")


@app.post("/chats/{chat_id}/messages")
async def create_message(chat_id: str, message:
                         CreateMessageRequest) -> CreateMessageResponse:
    message_number = await redis.incr('message_id_counter')
    sqids = Sqids()  # ?
    id = sqids.encode([message_number])
    message_id = f"MSG:{id}"
    created_at = datetime.now(timezone.utc).isoformat()
    new_message = CreateMessageResponse(chat_id=chat_id,
                                        id=message_id,
                                        text=message.text,
                                        ts=created_at)
    await redis.hset(f'chat:{chat_id}:message:{message_id}',
                     mapping={"chat_id": chat_id,
                              "id": message_id,
                              "text": message.text,
                              "ts": created_at})
    timestamp_score = datetime.fromisoformat(created_at).timestamp()
    await redis.zadd(f'chat:{chat_id}:messages', {message_id: timestamp_score})
    return new_message


class GetMessagesResponse(BaseModel):
    messages: list[CreateMessageResponse] = Field(
        description="All founded messages in this chat")


@app.get("/chats/{chat_id}/messages")
async def get_messages(
    chat_id: str,
    ts_message: str | None = Query(
        default=None,
        description="The time by which\
        you want to receive messages"),
        limit: int | None = Query(
        default=10, description="Maximum number of\
        returned messages")) -> GetMessagesResponse:
    chat_data = await redis.hgetall(f'chat:{chat_id}')
    if not chat_data:
        raise HTTPException(
            status_code=404,
            detail="Chat does not exist, please check if the id is correct")
    messages = []
    if ts_message:
        date_filter = datetime.fromisoformat(ts_message)
        date_filter = date_filter.replace(tzinfo=timezone.utc).timestamp()
    else:
        date_filter = "+inf"
    message_ids = await redis.zrangebyscore(f'chat:{chat_id}:messages', '-inf',
                                            date_filter, start=0, num=limit)
    messages = []
    for message_id in message_ids:
        message_data = await redis.hgetall(
            f'chat:{chat_id}:message:{message_id}')
        if message_data:
            messages.append(CreateMessageResponse(
                chat_id=message_data["chat_id"],
                id=message_data["id"],
                text=message_data["text"],
                ts=message_data["ts"]
            ))
    return GetMessagesResponse(messages=messages)


@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str) -> str:
    chat_data = await redis.hgetall(f'chat:{chat_id}')
    if not chat_data:
        raise HTTPException(
            status_code=404,
            detail="Chat does not exist, please check if the id is correct")
    message_keys = await redis.zrange(f'chat:{chat_id}:messages', 0, -1)
    for message_key in message_keys:
        await redis.delete(f'chat:{chat_id}:message:{message_key}')
    await redis.delete(f'chat:{chat_id}:messages')
