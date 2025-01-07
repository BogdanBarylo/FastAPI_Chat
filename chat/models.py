from pydantic import BaseModel, Field
from datetime import datetime


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
    ts: str = Field(description="Create time")


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


class GetMessagesResponse(BaseModel):
    messages: list[CreateMessageResponse] = Field(
        description="All founded messages in this chat"
    )
