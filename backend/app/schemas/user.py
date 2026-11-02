from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import UTCDatetime


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    has_completed_survey: bool = False
    created_at: UTCDatetime

    @classmethod
    def from_user(cls, user) -> "UserMe":
        p = user.profile
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            display_name=(p.display_name if p and p.display_name else user.username),
            avatar_url=p.avatar_url if p else None,
            has_completed_survey=user.survey is not None,
            created_at=user.created_at,
        )


class PublicUser(BaseModel):
    """Hồ sơ công khai: KHÔNG có email, cảm xúc, câu chuyện riêng tư."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    age_group: Optional[str] = None
    situation: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    is_online: bool = False
    last_seen: Optional[UTCDatetime] = None
    # friends | pending_sent | pending_received | None
    connection_status: Optional[str] = None
    connection_id: Optional[int] = None

    @classmethod
    def from_user(cls, user, connection_status: Optional[str] = None, connection_id: Optional[int] = None):
        p = user.profile
        return cls(
            id=user.id,
            username=user.username,
            display_name=(p.display_name if p and p.display_name else user.username),
            bio=p.bio if p else None,
            avatar_url=p.avatar_url if p else None,
            age_group=p.age_group if p else None,
            situation=p.situation if p else None,
            interests=list(p.interests or []) if p else [],
            is_online=bool(user.is_online),
            last_seen=user.last_seen,
            connection_status=connection_status,
            connection_id=connection_id,
        )


def display_name_of(user) -> str:
    p = user.profile
    return p.display_name if p and p.display_name else user.username
