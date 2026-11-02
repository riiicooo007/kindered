from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Notification, User
from app.schemas.notification import NotificationListOut, NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _unread_count(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
    ) or 0


@router.get("", response_model=NotificationListOut)
def list_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == me.id)
        .order_by(Notification.id.desc())
        .limit(limit)
    ).all()
    return NotificationListOut(
        items=[NotificationOut.model_validate(n) for n in rows],
        unread_count=_unread_count(db, me.id),
    )


@router.put("/read-all")
def mark_all_read(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    db.execute(
        update(Notification)
        .where(Notification.user_id == me.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return {"unread_count": 0}


@router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != me.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông báo")
    n.is_read = True
    db.commit()
    return n
