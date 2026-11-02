import logging
from typing import Any, Optional

import anyio.from_thread
from sqlalchemy.orm import Session

from app.models import Notification
from app.schemas.notification import NotificationOut
from app.services.ws_manager import manager

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    user_id: int,
    type_: str,
    message: str,
    link: Optional[str] = None,
    related_user_id: Optional[int] = None,
) -> Notification:
    """Thêm vào session và flush; người gọi chịu trách nhiệm commit."""
    n = Notification(user_id=user_id, type=type_, message=message, link=link, related_user_id=related_user_id)
    db.add(n)
    db.flush()
    return n


def notification_payload(n: Notification) -> dict[str, Any]:
    return {"type": "notification", "notification": NotificationOut.model_validate(n).model_dump(mode="json")}


def push_sync(user_id: int, payload: dict[str, Any]) -> None:
    """Đẩy realtime từ endpoint đồng bộ (chạy trong threadpool). Lỗi sẽ bị bỏ qua."""
    try:
        anyio.from_thread.run(manager.send_to_user, user_id, payload)
    except Exception:
        logger.debug("push_sync failed", exc_info=True)
