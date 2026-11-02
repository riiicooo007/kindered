from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import UTCDatetime
from app.schemas.user import PublicUser

MAX_MESSAGE_LENGTH = 2000


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: int
    content: str
    created_at: UTCDatetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)

    @field_validator("content")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tin nhắn không được để trống")
        return v


class ConversationCreate(BaseModel):
    user_id: int


class ConversationOut(BaseModel):
    id: int
    other_user: PublicUser
    last_message: Optional[MessageOut] = None
    created_at: UTCDatetime
