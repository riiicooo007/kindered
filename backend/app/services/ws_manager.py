import logging
from typing import Any, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Quản lý WebSocket trong bộ nhớ (chỉ đúng khi chạy 1 instance backend).

    active_connections[conversation_id][user_id] -> danh sách socket (nhiều tab)
    user_sockets[user_id]                       -> mọi socket của user (chat + notifications)
    """

    def __init__(self) -> None:
        self.active_connections: dict[int, dict[int, list[WebSocket]]] = {}
        self.user_sockets: dict[int, list[WebSocket]] = {}

    def register(self, ws: WebSocket, user_id: int, conversation_id: Optional[int] = None) -> bool:
        """Trả True nếu đây là kết nối ĐẦU TIÊN của user (user vừa online)."""
        first = not self.user_sockets.get(user_id)
        self.user_sockets.setdefault(user_id, []).append(ws)
        if conversation_id is not None:
            room = self.active_connections.setdefault(conversation_id, {})
            room.setdefault(user_id, []).append(ws)
        return first

    def unregister(self, ws: WebSocket, user_id: int, conversation_id: Optional[int] = None) -> bool:
        """Trả True nếu đây là kết nối CUỐI CÙNG của user (user vừa offline)."""
        sockets = self.user_sockets.get(user_id, [])
        if ws in sockets:
            sockets.remove(ws)
        if not sockets:
            self.user_sockets.pop(user_id, None)

        if conversation_id is not None:
            room = self.active_connections.get(conversation_id, {})
            user_list = room.get(user_id, [])
            if ws in user_list:
                user_list.remove(ws)
            if not user_list:
                room.pop(user_id, None)
            if not room:
                self.active_connections.pop(conversation_id, None)
        return user_id not in self.user_sockets

    def is_user_in_conversation(self, conversation_id: int, user_id: int) -> bool:
        return bool(self.active_connections.get(conversation_id, {}).get(user_id))

    @staticmethod
    async def _safe_send(ws: WebSocket, payload: dict[str, Any]) -> None:
        try:
            await ws.send_json(payload)
        except Exception:  # socket đã đóng; vòng lặp nhận sẽ tự dọn
            logger.debug("send_json failed", exc_info=True)

    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> None:
        for ws in list(self.user_sockets.get(user_id, [])):
            await self._safe_send(ws, payload)

    async def send_to_users(self, user_ids: list[int], payload: dict[str, Any]) -> None:
        for uid in user_ids:
            await self.send_to_user(uid, payload)

    async def broadcast_to_conversation(self, conversation_id: int, payload: dict[str, Any]) -> None:
        for sockets in list(self.active_connections.get(conversation_id, {}).values()):
            for ws in list(sockets):
                await self._safe_send(ws, payload)


manager = ConnectionManager()
