from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Conversation, ConversationMember, Message, User
from app.schemas.chat import ConversationCreate, ConversationOut, MessageCreate, MessageOut
from app.schemas.user import PublicUser
from app.services.chat_service import deliver_message, get_or_create_conversation, is_member
from app.services.connection_service import are_friends

router = APIRouter(prefix="/chat", tags=["Chat"])


def _last_message(db: Session, conversation_id: int) -> Optional[Message]:
    return db.scalar(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id.desc()).limit(1)
    )


def _conversation_out(db: Session, conv: Conversation, other: User) -> ConversationOut:
    last = _last_message(db, conv.id)
    return ConversationOut(
        id=conv.id,
        other_user=PublicUser.from_user(other),
        last_message=MessageOut.model_validate(last) if last else None,
        created_at=conv.created_at,
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    my_convs = select(ConversationMember.conversation_id).where(ConversationMember.user_id == me.id)
    others = db.scalars(
        select(ConversationMember).where(
            ConversationMember.conversation_id.in_(my_convs), ConversationMember.user_id != me.id
        )
    ).all()
    items = [
        _conversation_out(db, db.get(Conversation, m.conversation_id), db.get(User, m.user_id)) for m in others
    ]
    items.sort(key=lambda c: c.last_message.created_at if c.last_message else c.created_at, reverse=True)
    return items


@router.post("/conversations", response_model=ConversationOut)
def open_conversation(body: ConversationCreate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if body.user_id == me.id:
        raise HTTPException(status_code=400, detail="Không thể trò chuyện với chính mình")
    other = db.get(User, body.user_id)
    if other is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if not are_friends(db, me.id, other.id):
        raise HTTPException(status_code=403, detail="Chỉ có thể trò chuyện với người đã kết nối")
    conv = get_or_create_conversation(db, me.id, other.id)
    return _conversation_out(db, conv, other)


def _require_member(db: Session, conversation_id: int, me: User) -> None:
    if not is_member(db, conversation_id, me.id):
        raise HTTPException(status_code=403, detail="Bạn không thuộc cuộc trò chuyện này")


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    before_id: Optional[int] = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    _require_member(db, conversation_id, me)
    stmt = select(Message).where(Message.conversation_id == conversation_id)
    if before_id is not None:
        stmt = stmt.where(Message.id < before_id)
    rows = list(db.scalars(stmt.order_by(Message.id.desc()).limit(limit)))
    rows.reverse()  # trả theo thứ tự cũ -> mới
    return rows


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut, status_code=201)
async def send_message(
    conversation_id: int,
    body: MessageCreate,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    """Fallback REST khi WebSocket gặp sự cố. Vẫn phát realtime cho các socket đang mở."""
    if not await run_in_threadpool(is_member, db, conversation_id, me.id):
        raise HTTPException(status_code=403, detail="Bạn không thuộc cuộc trò chuyện này")
    return await deliver_message(conversation_id, me.id, body.content)
