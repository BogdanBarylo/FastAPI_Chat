from fastapi import Query, HTTPException, FastAPI, WebSocket
from chat.models import (
    CreateChatRequest,
    CreateChatResponse,
    CreateMessageRequest,
    CreateMessageResponse,
    GetMessagesResponse,
)
from datetime import datetime, timezone
from chat.db import (
    get_chat_id,
    get_message_id,
    get_format_time,
    save_chat_to_db,
    save_message_to_db,
    check_chat_in_db,
    get_all_filtered_message_ids,
    get_all_filtered_messages,
    get_chat_data,
    get_all_messages_ids,
    del_chat,
)
from chat.db import redis

app = FastAPI()


@app.post("/chats")
async def create_chat(chat: CreateChatRequest) -> CreateChatResponse:
    chat_id = await get_chat_id()
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


@app.post("/chats/{chat_id}/messages")
async def create_message(
    chat_id: str, message: CreateMessageRequest
) -> CreateMessageResponse:
    message_id = await get_message_id()
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
    await redis.publish(
        f"chat:{chat_id}:messages", new_message.model_dump_json()
    )
    return new_message


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
    message_ids = await get_all_filtered_message_ids(
        chat_id, date_filter, limit
    )
    messages = []
    message_data_list = await get_all_filtered_messages(chat_id, message_ids)
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
    await del_chat(chat_id, message_ids)


@app.websocket("/chats/{chat_id}/messages/new")
async def show_new_message(websocket: WebSocket, chat_id: str):
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"chat:{chat_id}:messages")
    await websocket.accept()
    async for message in pubsub.listen():
        if message["type"] == "message":
            await websocket.send_text(message["data"])
    await pubsub.unsubscribe(f"chat:{chat_id}:messages")
    await pubsub.close()
