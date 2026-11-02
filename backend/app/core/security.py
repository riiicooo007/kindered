from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from app.core.config import settings


class TokenError(Exception):
    def __init__(self, message: str, expired: bool = False):
        super().__init__(message)
        self.expired = expired


def hash_password(password: str) -> str:
    # bcrypt chỉ dùng tối đa 72 byte đầu của mật khẩu
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: Optional[str]) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int, expires_minutes: Optional[int] = None) -> str:
    now = datetime.now(timezone.utc)
    minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else expires_minutes
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> int:
    """Trả về user_id hoặc raise TokenError (hết hạn / không hợp lệ)."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise TokenError("Token đã hết hạn", expired=True)
    except jwt.PyJWTError:
        raise TokenError("Token không hợp lệ")
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise TokenError("Token không hợp lệ")
