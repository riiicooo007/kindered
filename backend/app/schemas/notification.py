from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import UTCDatetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    message: str
    link: Optional[str] = None
    related_user_id: Optional[int] = None
    is_read: bool
    created_at: UTCDatetime


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    unread_count: int
