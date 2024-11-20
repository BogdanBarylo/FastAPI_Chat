from fastapi import Query, HTTPException, FastAPI
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from chat.db import (
    get_id,
    get_format_time,
    save_chat_to_db,
    save_message_to_db,
    check_chat_in_db,
    get_all_filtred_message_ids,
    get_all_fitred_messages,
    get_chat_data,
    get_all_messages_ids,
    del_chat_from_db,
)

app = FastAPI()


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
    chat_id = await get_id("chat")
    ts = datetime.now(timezone.utc)
    formated_ts = get_format_time(ts)
    url = f"/chats/{chat_id}"
    chat_data = {
        "chat_id": chat_id,
        "name": chat.name,
        "ts": formated_ts,
    }
    await save_chat_to_db(chat_data)
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
    message_id = await get_id("message")
    ts = datetime.now(timezone.utc)
    formated_ts = get_format_time(ts)
    message_data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": message.text,
            "ts": formated_ts,
        }
    await save_message_to_db(message_data, ts)
    new_message = CreateMessageResponse(
        chat_id=chat_id,
        message_id=message_id,
        text=message.text,
        ts=formated_ts,
    )
    return new_message


class GetMessagesResponse(BaseModel):
    messages: list[CreateMessageResponse] = Field(
        description="All founded messages in this chat"
    )


GetMessagesTsParam = Query(
    default=None, description="The time by which you want to receive messages"
)

GetMessagesLimitParam = Query(
    default=10, description="Maximum number of returned messages"
)


@app.get("/chats/{chat_id}/messages")
async def get_messages(
    chat_id: str,
    ts_message: datetime | None = GetMessagesTsParam,
    limit: int = GetMessagesLimitParam,
) -> GetMessagesResponse:
    chat_exists = await check_chat_in_db(chat_id)
    if not chat_exists:
        raise HTTPException(
            status_code=404,
            detail="Chat does not exist, please check if the id is correct",
        )
    messages = []
    if ts_message:
        date_filter = ts_message.replace(tzinfo=timezone.utc).timestamp()
    else:
        date_filter = "+inf"
    message_ids = await get_all_filtred_message_ids(chat_id, date_filter, limit)
    messages = []
    message_data_list = await get_all_fitred_messages(chat_id, message_ids)
    for message_data in message_data_list:
        if message_data:
            message_obj = CreateMessageResponse.model_validate_json(
                message_data
            )
            messages.append(message_obj)
    return GetMessagesResponse(messages=messages)


@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    chat_data = await get_chat_data(chat_id)
    if not chat_data:
        raise HTTPException(
            status_code=404,
            detail="Chat does not exist, please check if the id is correct",
        )
    message_ids = await get_all_messages_ids(chat_id)
    await del_chat_from_db(chat_id, message_ids)
