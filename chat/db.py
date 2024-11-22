from sqids import Sqids
from chat.conf import redis
from datetime import datetime
import json

# def make_pipeline():
#     def wrapper(*args, **kwargs):


async def get_id(obj: str) -> str:
    sqids = Sqids()
    if obj == "chat":
        chat_number = await redis.incr("chat_id_counter")
        chat_id = f"CHT:{sqids.encode([chat_number])}"
        return chat_id
    elif obj == "message":
        message_number = await redis.incr("message_id_counter")
        message_id = f"MSG:{sqids.encode([message_number])}"
        return message_id


def get_format_time(ts: datetime) -> str:
    formatted_ts = ts.strftime("%Y-%m-%dT%H:%M:%S")
    return formatted_ts


async def save_chat_to_db(chat_data: dict) -> None:
    await redis.hset(
        f"chat:{chat_data['chat_id']}",
        mapping={
            "chat_id": chat_data["chat_id"],
            "name": chat_data["name"],
            "ts": chat_data["ts"],
        },
    )


async def save_message_to_db(message_data: dict, ts: datetime) -> None:
    async with redis.pipeline(transaction=True) as pipe:
        message_data_serialized = json.dumps(message_data)
        await redis.hset(
            f"chat:{message_data['chat_id']}:message",
            message_data["message_id"],
            message_data_serialized,
        )
        await redis.zadd(
            f"chat:{message_data['chat_id']}:messages:ts",
            {message_data["message_id"]: ts.timestamp()},
        )
        await pipe.execute()


async def check_chat_in_db(chat_id: str) -> bool:
    check = await redis.exists(f"chat:{chat_id}")
    return check


async def get_all_filtred_message_ids(
    chat_id: str, date_filter: str, limit: int
) -> list:
    return await redis.zrangebyscore(
        f"chat:{chat_id}:messages:ts", "-inf", date_filter, start=0, num=limit
    )


async def get_all_fitred_messages(chat_id: str, message_ids: list) -> list:
    async with redis.pipeline() as pipe:
        for message_id in message_ids:
            pipe.hget(f"chat:{chat_id}:message", message_id)
        message_data_list = await pipe.execute()
    return message_data_list


async def get_chat_data(chat_id: str) -> dict:
    chat_data = await redis.hgetall(f"chat:{chat_id}")
    return chat_data


async def get_all_messages_ids(chat_id: str) -> list:
    return await redis.zrange(f"chat:{chat_id}:messages:ts", 0, -1)


async def del_chat_from_db(chat_id: str, message_ids: list) -> None:
    async with redis.pipeline(transaction=True) as pipe:
        for message_id in message_ids:
            await redis.delete(f"chat:{chat_id}:message:{message_id}")
        await redis.delete(f"chat:{chat_id}:messages:ts")
        await redis.delete(f"chat:{chat_id}")
        await pipe.execute()
