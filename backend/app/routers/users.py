from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.user import PublicUser, UserMe
from app.services.connection_service import status_map

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserMe)
def read_me(me: User = Depends(get_current_user)):
    return UserMe.from_user(me)


@router.get("/{user_id}", response_model=PublicUser)
def read_public_user(user_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    label, conn_id = status_map(db, me.id, [user.id]).get(user.id, (None, None))
    return PublicUser.from_user(user, label, conn_id)
