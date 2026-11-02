from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased
from starlette.concurrency import run_in_threadpool

from app.db.session import SessionLocal
from app.models import (
    Conversation, ConversationMember, Message, Notification, NotificationType, User,
)
from app.schemas.chat import MessageOut
from app.schemas.user import display_name_of
from app.services.notification_service import create_notification, notification_payload
from app.services.ws_manager import manager


def is_member(db: Session, conversation_id: int, user_id: int) -> bool:
    return (
        db.scalar(
            select(ConversationMember.id).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
        )
        is not None
    )


def other_member_ids(db: Session, conversation_id: int, user_id: int) -> list[int]:
    return list(
        db.scalars(
            select(ConversationMember.user_id).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id != user_id,
            )
        )
    )


def find_conversation(db: Session, a: int, b: int) -> Optional[Conversation]:
    cm1, cm2 = aliased(ConversationMember), aliased(ConversationMember)
    conv_id = db.scalar(
        select(cm1.conversation_id)
        .join(cm2, cm1.conversation_id == cm2.conversation_id)
        .where(cm1.user_id == a, cm2.user_id == b)
        .limit(1)
    )
    return db.get(Conversation, conv_id) if conv_id is not None else None


def get_or_create_conversation(db: Session, a: int, b: int) -> Conversation:
    conv = find_conversation(db, a, b)
    if conv is not None:
        return conv
    conv = Conversation()
    db.add(conv)
    db.flush()
    db.add_all(
        [
            ConversationMember(conversation_id=conv.id, user_id=a),
            ConversationMember(conversation_id=conv.id, user_id=b),
        ]
    )
    db.commit()
    return conv


def _persist_message(conversation_id: int, sender_id: int, content: str) -> tuple[dict, list[int], str]:
    with SessionLocal() as db:
        msg = Message(conversation_id=conversation_id, sender_id=sender_id, content=content)
        db.add(msg)
        db.commit()
        sender = db.get(User, sender_id)
        recipients = other_member_ids(db, conversation_id, sender_id)
        data = MessageOut.model_validate(msg).model_dump(mode="json")
        return data, recipients, display_name_of(sender)


def _notify_new_message(recipient_id: int, conversation_id: int, sender_name: str, sender_id: int) -> Optional[dict]:
    link = f"/chat/{conversation_id}"
    with SessionLocal() as db:
        already = db.scalar(
            select(Notification.id)
            .where(
                Notification.user_id == recipient_id,
                Notification.type == NotificationType.NEW_MESSAGE,
                Notification.link == link,
                Notification.is_read.is_(False),
            )
            .limit(1)
        )
        if already is not None:  # tránh spam: chỉ 1 thông báo chưa đọc cho mỗi cuộc trò chuyện
            return None
        n = create_notification(
            db, recipient_id, NotificationType.NEW_MESSAGE,
            f"{sender_name} đã gửi cho bạn một tin nhắn", link=link, related_user_id=sender_id,
        )
        db.commit()
        return notification_payload(n)


async def deliver_message(conversation_id: int, sender_id: int, content: str) -> dict[str, Any]:
    """Lưu tin nhắn, phát cho mọi socket trong phòng, thông báo cho người nhận đang không mở phòng."""
    data, recipients, sender_name = await run_in_threadpool(_persist_message, conversation_id, sender_id, content)
    await manager.broadcast_to_conversation(conversation_id, {"type": "message", "message": data})
    for rid in recipients:
        if not manager.is_user_in_conversation(conversation_id, rid):
            payload = await run_in_threadpool(_notify_new_message, rid, conversation_id, sender_name, sender_id)
            if payload is not None:
                await manager.send_to_user(rid, payload)
    return data
