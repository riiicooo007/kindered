from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import Connection, ConnectionStatus


def get_between(db: Session, a: int, b: int) -> Optional[Connection]:
    return db.scalar(
        select(Connection).where(
            or_(
                and_(Connection.requester_id == a, Connection.receiver_id == b),
                and_(Connection.requester_id == b, Connection.receiver_id == a),
            )
        )
    )


def relation_label(conn: Connection, me_id: int) -> Optional[str]:
    """friends | pending_sent | pending_received | None (bị từ chối coi như chưa kết nối)."""
    if conn.status == ConnectionStatus.ACCEPTED:
        return "friends"
    if conn.status == ConnectionStatus.PENDING:
        return "pending_sent" if conn.requester_id == me_id else "pending_received"
    return None


def status_map(db: Session, me_id: int, other_ids: list[int]) -> dict[int, tuple[Optional[str], int]]:
    """{other_id: (label, connection_id)} cho các user có quan hệ với mình."""
    if not other_ids:
        return {}
    rows = db.scalars(
        select(Connection).where(
            or_(
                and_(Connection.requester_id == me_id, Connection.receiver_id.in_(other_ids)),
                and_(Connection.receiver_id == me_id, Connection.requester_id.in_(other_ids)),
            )
        )
    )
    result: dict[int, tuple[Optional[str], int]] = {}
    for c in rows:
        other = c.receiver_id if c.requester_id == me_id else c.requester_id
        result[other] = (relation_label(c, me_id), c.id)
    return result


def are_friends(db: Session, a: int, b: int) -> bool:
    conn = get_between(db, a, b)
    return conn is not None and conn.status == ConnectionStatus.ACCEPTED


def friend_ids(db: Session, user_id: int) -> list[int]:
    rows = db.scalars(
        select(Connection).where(
            Connection.status == ConnectionStatus.ACCEPTED,
            or_(Connection.requester_id == user_id, Connection.receiver_id == user_id),
        )
    )
    return [c.receiver_id if c.requester_id == user_id else c.requester_id for c in rows]
