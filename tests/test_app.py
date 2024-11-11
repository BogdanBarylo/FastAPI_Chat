import pytest
from unittest.mock import patch
import json


# @pytest.mark.asyncio
# async def test_create_chat(client, redis, test_data):
#     with patch("chat.main.get_id") as get_id:
#         get_id.return_value = "test_chat_id"
#         response = await client.post("/chats", json={"name": "test_chat"})
#         response_data = response.json()
#         assert response.status_code == 200
#         assert response_data["name"] == "test_chat"

#         chat_data = await redis.hgetall(
#             f'chat:{response_data["chat_id"]}'
#         )
#         assert chat_data["name"] == "test_chat"
#         assert chat_data["chat_id"] == "test_chat_id"
#         assert chat_data["url"] == response_data["url"] # убрать url
#         ts_response = datetime.fromisoformat(response_data["ts"].replace("Z", "+00:00"))
#         ts_chat = datetime.fromisoformat(chat_data["ts"])
#         assert ts_chat == ts_response
#         test_data["chat_id"] = chat_data["chat_id"]
#         test_data["chat_data"] = chat_data


@pytest.mark.asyncio
async def test_create_chat(client, redis):
    with patch("chat.main.get_id") as get_id:
        get_id.return_value = "test_chat_id"
        with patch("chat.main.get_time") as get_time:
            get_time.return_value = "2024-11-11T13:36:40"
            response = await client.post("/chats", json={"name": "test_chat"})
            response_data = response.json()
            chat_data = await redis.hgetall(
                f'chat:{response_data["chat_id"]}'
            )
            assert response.status_code == 200
            assert response_data["name"] == "test_chat"
            assert chat_data["name"] == "test_chat"
            assert chat_data["chat_id"] == "CHT:test_chat_id"
            assert chat_data["ts"] == "2024-11-11T13:36:40"

# @pytest.mark.asyncio
# async def test_create_message(client, redis, test_data):
#     with patch("chat.main.get_id") as get_id:
#         get_id.return_value = "test_message_id"
#         response = await client.post(f"/chats/{test_data['chat_id']}/messages", json={"text": "Hi"})
#         response_data = response.json()
#         message_data = await redis.hget(f"chat:{test_data['chat_id']}:message", response_data["message_id"])
#         message_data = json.loads(message_data)
#         assert response.status_code == 200
#         assert message_data["chat_id"] == test_data["chat_id"]
#         assert message_data["text"] == response_data["text"]
#         assert message_data["message_id"] == response_data["message_id"]
#         ts_response = datetime.fromisoformat(response_data["ts"].replace("Z", "+00:00"))
#         ts_message = datetime.fromisoformat(message_data["ts"])
#         assert ts_message == ts_response

