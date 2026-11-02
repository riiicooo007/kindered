from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Connection, ConnectionStatus, NotificationType, User
from app.schemas.connection import ConnectionItem, ConnectionRequestsOut
from app.schemas.user import PublicUser, display_name_of
from app.services.connection_service import get_between, relation_label
from app.services.notification_service import create_notification, notification_payload, push_sync

router = APIRouter(prefix="/connections", tags=["Connections"])


def _item(db: Session, conn: Connection, me_id: int) -> ConnectionItem:
    other_id = conn.receiver_id if conn.requester_id == me_id else conn.requester_id
    other = db.get(User, other_id)
    return ConnectionItem(
        connection_id=conn.id,
        status=conn.status,
        direction="sent" if conn.requester_id == me_id else "received",
        created_at=conn.created_at,
        user=PublicUser.from_user(other, relation_label(conn, me_id), conn.id),
    )


@router.get("/friends", response_model=list[ConnectionItem])
def list_friends(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Connection)
        .where(
            Connection.status == ConnectionStatus.ACCEPTED,
            or_(Connection.requester_id == me.id, Connection.receiver_id == me.id),
        )
        .order_by(Connection.updated_at.desc())
    )
    return [_item(db, c, me.id) for c in rows]


@router.get("/requests", response_model=ConnectionRequestsOut)
def list_requests(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    received = db.scalars(
        select(Connection)
        .where(Connection.receiver_id == me.id, Connection.status == ConnectionStatus.PENDING)
        .order_by(Connection.created_at.desc())
    )
    sent = db.scalars(
        select(Connection)
        .where(Connection.requester_id == me.id, Connection.status == ConnectionStatus.PENDING)
        .order_by(Connection.created_at.desc())
    )
    return ConnectionRequestsOut(
        received=[_item(db, c, me.id) for c in received],
        sent=[_item(db, c, me.id) for c in sent],
    )


@router.post("/request/{user_id}", response_model=ConnectionItem, status_code=201)
def send_request(user_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if user_id == me.id:
        raise HTTPException(status_code=400, detail="Không thể kết nối với chính mình")
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    conn = get_between(db, me.id, user_id)
    if conn is not None:
        if conn.status == ConnectionStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="Hai bạn đã là bạn bè")
        if conn.status == ConnectionStatus.PENDING:
            if conn.requester_id == me.id:
                raise HTTPException(status_code=400, detail="Bạn đã gửi lời mời cho người này rồi")
            raise HTTPException(status_code=400, detail="Người này đã gửi lời mời cho bạn, hãy chấp nhận")
        # từng bị từ chối -> cho phép gửi lại
        conn.requester_id, conn.receiver_id, conn.status = me.id, user_id, ConnectionStatus.PENDING
    else:
        conn = Connection(requester_id=me.id, receiver_id=user_id, status=ConnectionStatus.PENDING)
        db.add(conn)

    n = create_notification(
        db, user_id, NotificationType.CONNECTION_REQUEST,
        f"{display_name_of(me)} muốn kết nối với bạn", link="/connections", related_user_id=me.id,
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Lời mời đã tồn tại")
    push_sync(user_id, notification_payload(n))
    return _item(db, conn, me.id)


def _get_incoming_pending(db: Session, connection_id: int, me: User) -> Connection:
    conn = db.get(Connection, connection_id)
    if conn is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lời mời")
    if conn.receiver_id != me.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xử lý lời mời này")
    if conn.status != ConnectionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Lời mời này đã được xử lý")
    return conn


@router.put("/{connection_id}/accept", response_model=ConnectionItem)
def accept_request(connection_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    conn = _get_incoming_pending(db, connection_id, me)
    conn.status = ConnectionStatus.ACCEPTED
    n = create_notification(
        db, conn.requester_id, NotificationType.CONNECTION_ACCEPTED,
        f"{display_name_of(me)} đã chấp nhận lời mời kết nối của bạn", link="/connections", related_user_id=me.id,
    )
    db.commit()
    push_sync(conn.requester_id, notification_payload(n))
    return _item(db, conn, me.id)


@router.put("/{connection_id}/reject", response_model=ConnectionItem)
def reject_request(connection_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    conn = _get_incoming_pending(db, connection_id, me)
    conn.status = ConnectionStatus.REJECTED
    db.commit()
    return _item(db, conn, me.id)
