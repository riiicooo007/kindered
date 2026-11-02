import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from starlette.concurrency import run_in_threadpool

from app.core.security import TokenError, decode_access_token
from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models import User
from app.schemas.chat import MAX_MESSAGE_LENGTH
from app.schemas.common import ensure_utc
from app.services.chat_service import deliver_message, is_member
from app.services.connection_service import friend_ids
from app.services.ws_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


def _authenticate(token: str, conversation_id: Optional[int]) -> Optional[int]:
    """Xác thực JWT + quyền thành viên TRƯỚC khi accept. None = từ chối."""
    try:
        user_id = decode_access_token(token)
    except TokenError:
        return None
    with SessionLocal() as db:
        if db.get(User, user_id) is None:
            return None
        if conversation_id is not None and not is_member(db, conversation_id, user_id):
            return None
    return user_id


def _set_presence(user_id: int, online: bool) -> tuple[Optional[datetime], list[int]]:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            return None, []
        user.is_online = online
        if not online:
            user.last_seen = utcnow()
        db.commit()
        return user.last_seen, friend_ids(db, user_id)


async def _announce(user_id: int, online: bool) -> None:
    last_seen, friends = await run_in_threadpool(_set_presence, user_id, online)
    payload: dict = {"type": "user_status", "user_id": user_id, "is_online": online}
    if not online and last_seen is not None:
        payload["last_seen"] = ensure_utc(last_seen).isoformat()
    await manager.send_to_users(friends, payload)


async def _handle(ws: WebSocket, user_id: int, conversation_id: Optional[int], raw: str) -> None:
    try:
        data = json.loads(raw)
    except ValueError:
        data = None
    if not isinstance(data, dict):
        await ws.send_json({"type": "error", "detail": "Dữ liệu không hợp lệ"})
        return

    kind = data.get("type")
    if kind == "ping":
        await ws.send_json({"type": "pong"})
    elif kind == "message" and conversation_id is not None:
        content = str(data.get("content", "")).strip()
        if not content or len(content) > MAX_MESSAGE_LENGTH:
            await ws.send_json({"type": "error", "detail": f"Tin nhắn phải từ 1 đến {MAX_MESSAGE_LENGTH} ký tự"})
        else:
            await deliver_message(conversation_id, user_id, content)
    else:
        await ws.send_json({"type": "error", "detail": "Loại sự kiện không được hỗ trợ"})


async def _serve(ws: WebSocket, user_id: int, conversation_id: Optional[int]) -> None:
    await ws.accept()
    if manager.register(ws, user_id, conversation_id):
        await _announce(user_id, True)
    try:
        while True:
            await _handle(ws, user_id, conversation_id, await ws.receive_text())
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WebSocket error")
    finally:
        if manager.unregister(ws, user_id, conversation_id):
            try:
                await _announce(user_id, False)
            except Exception:
                logger.exception("Failed to announce offline status")


@router.websocket("/ws/chat/{conversation_id}")
async def chat_socket(websocket: WebSocket, conversation_id: int, token: str = Query(default="")):
    user_id = await run_in_threadpool(_authenticate, token, conversation_id)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await _serve(websocket, user_id, conversation_id)


@router.websocket("/ws/notifications")
async def notifications_socket(websocket: WebSocket, token: str = Query(default="")):
    """Kênh toàn cục: thông báo realtime + trạng thái online của bạn bè."""
    user_id = await run_in_threadpool(_authenticate, token, None)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await _serve(websocket, user_id, None)
