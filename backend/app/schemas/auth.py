import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserMe

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    email: str = Field(max_length=255)
    username: str = Field(pattern=r"^[A-Za-z0-9_.]{3,30}$")
    password: str = Field(min_length=8, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Email không hợp lệ")
        return v

    @field_validator("display_name")
    @classmethod
    def _strip_name(cls, v: Optional[str]) -> Optional[str]:
        v = v.strip() if v else None
        return v or None


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255, description="Username hoặc email")
    password: str = Field(min_length=1, max_length=128)


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=10)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserMe
