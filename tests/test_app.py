import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json
from chat.db import get_chat_id, get_message_id, get_format_time


@pytest.mark.asyncio
async def test_get_chat_id():
    with patch("chat.db.Sqids") as s, patch("chat.db.redis") as r:
        r.incr = AsyncMock(return_value=1)
        s.return_value.encode.return_value = "test_chat_id"
        chat_id = await get_chat_id()
        assert chat_id == "CHT:test_chat_id"
        r.incr.assert_called_once_with("chat_id_counter")
        s.return_value.encode.assert_called_once_with([1])


@pytest.mark.asyncio
async def test_get_message_id():
    with patch("chat.db.Sqids") as s, patch("chat.db.redis") as r:
        r.incr = AsyncMock(return_value=1)
        s.return_value.encode.return_value = "test_message_id"
        message_id = await get_message_id()
        assert message_id == "MSG:test_message_id"
        r.incr.assert_called_once_with("message_id_counter")
        s.return_value.encode.assert_called_once_with([1])


def test_get_format_time():
    test_datetime = datetime(2023, 1, 1, 12, 30, 45)
    formatted_time = get_format_time(test_datetime)
    assert formatted_time == "2023-01-01T12:30:45"


@pytest.mark.asyncio
async def test_create_chat(client, redis, monkeypatch):
    get_chat_id = AsyncMock()
    get_chat_id.return_value = "CHT:test_chat_id"
    monkeypatch.setattr("chat.api.get_chat_id", get_chat_id)

    get_format_time = Mock()
    get_format_time.return_value = "2024-11-11T13:36:40"
    monkeypatch.setattr("chat.api.get_format_time", get_format_time)
    response = await client.post("/chats", json={"name": "test_chat"})
    assert response.status_code == 200
    response_data = response.json()
    chat_data = await redis.hgetall(f'chat:{response_data["chat_id"]}')
    assert response_data["name"] == "test_chat"
    assert chat_data == {
        "name": "test_chat",
        "chat_id": "CHT:test_chat_id",
        "ts": "2024-11-11T13:36:40",
    }


@pytest.mark.asyncio
async def test_create_message(client, redis, monkeypatch, test_data):
    get_message_id = AsyncMock()
    get_message_id.return_value = "MSG:test_message_id"
    monkeypatch.setattr("chat.api.get_message_id", get_message_id)

    get_format_time = Mock()
    get_format_time.return_value = "2024-11-11T13:38:40"
    monkeypatch.setattr("chat.api.get_format_time", get_format_time)

    response = await client.post(
        "/chats/CHT:test_id/messages", json={"text": "Hi"}
    )
    assert response.status_code == 200
    message_data = await redis.hget(
        "chat:CHT:test_id:message", "MSG:test_message_id"
    )
    message_data = json.loads(message_data)
    assert message_data == {
        "chat_id": "CHT:test_id",
        "text": "Hi",
        "message_id": "MSG:test_message_id",
        "ts": "2024-11-11T13:38:40",
    }


@pytest.mark.asyncio
async def test_get_messages(client, test_data):
    response = await client.get("/chats/CHT:test_id/messages")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data == {
        "messages": [
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
    }


@pytest.mark.asyncio
async def test_get_messages_not_existent(client):
    response = await client.get("/chats/CHT:notexistent/messages")
    assert response.status_code == 404
    response_data = response.json()
    assert response_data == {
        "detail": "Chat does not exist, please check if the id is correct"
    }


@pytest.mark.asyncio
async def test_get_messages_with_limit(client, test_data):
    response = await client.get("/chats/CHT:test_id/messages?limit=1")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data == {
        "messages": [
            {
                "chat_id": "CHT:test_id",
                "message_id": "MSG:test_id_1",
                "text": "hi, its test 1!",
                "ts": "2024-11-11T13:37:40",
            }
        ]
    }


@pytest.mark.asyncio
async def test_get_messages_with_filter(client, test_data):
    response = await client.get(
        "/chats/CHT:test_id/messages?ts_message=2024-11-11T13:38:00"
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data == {
        "messages": [
            {
                "chat_id": "CHT:test_id",
                "message_id": "MSG:test_id_1",
                "text": "hi, its test 1!",
                "ts": "2024-11-11T13:37:40",
            }
        ]
    }


@pytest.mark.asyncio
async def test_del_chat(client, test_data):
    response = await client.delete("/chats/CHT:test_id")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data is None
    response = await client.delete("/chats/CHT:test_id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_show_new_message(
    websocket_client, websocket_redis, monkeypatch
):
    handle_message_mock = AsyncMock()
    monkeypatch.setattr("chat.api.handle_message", handle_message_mock)
    async with websocket_client.websocket_connect(
        "/chats/CHT:test_id/messages/new"
    ) as websocket:
        await websocket.send_text("Hello from test!")
        await websocket_redis.publish(
            "chat:CHT:test_id:messages", "Hello from test"
        )
        msg = await websocket.receive_text()
        assert msg == "Hello from test"
    handle_message_mock.assert_awaited_once_with(
        "CHT:test_id", "Hello from test!"
    )
