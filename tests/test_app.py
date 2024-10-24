import pytest

@pytest.mark.asyncio
async def test_create_chat(get_client, redis_test_connect):
    response = get_client.post("/chats", json={"name": "test_chat"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "test_chat"
    assert "id" in response_data
    assert "url" in response_data
    assert "ts" in response_data
    chat_data = await redis_test_connect.hgetall(f'chat:{response_data["id"]}')
    assert chat_data["name"] == "test_chat"
    assert chat_data["id"] == response_data["id"]
    assert chat_data["url"] == response_data["url"]
    assert chat_data["ts"] == response_data["ts"]