from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Profile, User
from app.schemas.profile import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])


def _ensure_profile(db: Session, me: User) -> Profile:
    if me.profile is None:
        me.profile = Profile(display_name=me.username, interests=[])
        db.commit()
    return me.profile


@router.get("/me", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    return _ensure_profile(db, me)


@router.put("/me", response_model=ProfileOut)
def update_profile(body: ProfileUpdate, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    profile = _ensure_profile(db, me)
    for key, value in body.model_dump(exclude_unset=True).items():
        if value is None and key == "display_name":
            continue
        setattr(profile, key, value)
    db.commit()
    return profile
