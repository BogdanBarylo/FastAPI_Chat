import pytest
from unittest.mock import Mock, AsyncMock
import json



@pytest.mark.asyncio
async def test_create_chat(client, redis, monkeypatch):
    get_id = AsyncMock()
    get_id.return_value = "CHT:test_chat_id"
    monkeypatch.setattr("chat.main.get_id", get_id)

    get_format_time = Mock()
    get_format_time.return_value = "2024-11-11T13:36:40"
    monkeypatch.setattr("chat.main.get_format_time", get_format_time)
    response = await client.post("/chats", json={"name": "test_chat"})
    assert response.status_code == 200
    response_data = response.json()
    chat_data = await redis.hgetall(f'chat:{response_data["chat_id"]}')
    print(chat_data)
    assert response_data["name"] == "test_chat"
    assert chat_data == {
        "name": "test_chat",
        "chat_id": "CHT:test_chat_id",
        "ts": "2024-11-11T13:36:40",
    }


# @pytest.mark.asyncio
# async def test_create_message(client, redis, monkeypatch, test_data):
#     get_id = Mock()
#     get_id.return_value = "test_message_id"
#     monkeypatch.setattr("chat.db.get_id", get_id)

#     get_format_time = Mock()
#     get_format_time.return_value = "2024-11-11T13:38:40"
#     monkeypatch.setattr("chat.db.get_format_time", get_format_time)

#     response = await client.post(
#         "/chats/CHT:test_id/messages", json={"text": "Hi"}
#     )
#     assert response.status_code == 200
#     message_data = await redis.hget(
#         "chat:CHT:test_id:message", "MSG:test_message_id"
#     )
#     message_data = json.loads(message_data)
#     assert message_data == {
#         "chat_id": "CHT:test_id",
#         "text": "Hi",
#         "message_id": "MSG:test_message_id",
#         "ts": "2024-11-11T13:38:40",
#     }


# @pytest.mark.asyncio
# async def test_get_messages(client, test_data):
#     response = await client.get("/chats/CHT:test_id/messages")
#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data == {
#         "messages": [
#             {
#                 "chat_id": "CHT:test_id",
#                 "message_id": "MSG:test_id_1",
#                 "text": "hi, its test 1!",
#                 "ts": "2024-11-11T13:37:40",
#             },
#             {
#                 "chat_id": "CHT:test_id",
#                 "message_id": "MSG:test_id_2",
#                 "text": "hello again, test 2!",
#                 "ts": "2024-11-11T13:39:00",
#             },
#         ]
#     }


# @pytest.mark.asyncio
# async def test_get_messages_with_limit(client, test_data):
#     response = await client.get("/chats/CHT:test_id/messages?limit=1")
#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data == {
#         "messages": [
#             {
#                 "chat_id": "CHT:test_id",
#                 "message_id": "MSG:test_id_1",
#                 "text": "hi, its test 1!",
#                 "ts": "2024-11-11T13:37:40",
#             }
#         ]
#     }


# # @pytest.mark.asyncio
# # async def test_get_messages_with_filter(client, test_data):
# #     response = await client.get('/chats/CHT:test_id/messages?ts_message=2024-11-11T13:38:00')
# #     assert response.status_code == 200
# #     response_data = response.json()
# #     assert response_data == {"messages":[{"chat_id": "CHT:test_id", "message_id": "MSG:test_id_2", "text": "hello again, test 2!", "ts": "2024-11-11T13:39:00"}]}


# @pytest.mark.asyncio
# async def test_del_chat(client, test_data):
#     response = await client.delete("/chats/CHT:test_id")
#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data is None
#     response = await client.delete("/chats/CHT:test_id")
#     assert response.status_code == 404
