import re
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Profile, User
from app.schemas.auth import AuthResponse, GoogleLoginRequest, LoginRequest, RegisterRequest
from app.schemas.user import UserMe

router = APIRouter(prefix="/auth", tags=["Auth"])


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(access_token=create_access_token(user.id), user=UserMe.from_user(user))


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    username = body.username.lower()
    existing = db.scalar(select(User).where(or_(User.email == body.email, User.username == username)))
    if existing is not None:
        what = "Email" if existing.email == body.email else "Tên người dùng"
        raise HTTPException(status_code=409, detail=f"{what} đã được sử dụng")

    user = User(email=body.email, username=username, hashed_password=hash_password(body.password))
    user.profile = Profile(display_name=body.display_name or username, interests=[])
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email hoặc tên người dùng đã được sử dụng")
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    ident = body.identifier.strip().lower()
    user = db.scalar(select(User).where(or_(User.email == ident, User.username == ident)))
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")
    return _auth_response(user)


def _unique_username(db: Session, email: str) -> str:
    base = re.sub(r"[^a-z0-9_.]", "", email.split("@")[0].lower())[:20]
    if len(base) < 3:
        base = (base + "user")[:20]
    candidate = base
    while db.scalar(select(User.id).where(User.username == candidate)) is not None:
        candidate = f"{base}{secrets.randbelow(10000):04d}"
    return candidate


@router.post("/google", response_model=AuthResponse)
def google_login(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Đăng nhập Google chưa được cấu hình")
    try:
        from google.auth.transport import requests as g_requests
        from google.oauth2 import id_token

        info = id_token.verify_oauth2_token(body.id_token, g_requests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError:
        raise HTTPException(status_code=401, detail="Google ID token không hợp lệ")

    email = str(info.get("email", "")).lower()
    if not email or not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Email Google chưa được xác minh")
    google_id = str(info["sub"])

    user = db.scalar(select(User).where(User.google_id == google_id))
    if user is None:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:  # liên kết tài khoản email sẵn có với Google
            user.google_id = google_id
    if user is None:
        user = User(email=email, username=_unique_username(db, email), google_id=google_id)
        user.profile = Profile(
            display_name=(info.get("name") or user.username)[:100],
            avatar_url=info.get("picture"),
            interests=[],
        )
        db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Không thể tạo tài khoản, vui lòng thử lại")
    return _auth_response(user)
