from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import CleanList, UTCDatetime


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    age_group: Optional[str] = None
    situation: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    updated_at: Optional[UTCDatetime] = None


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=500)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    age_group: Optional[str] = Field(default=None, max_length=50)
    situation: Optional[str] = Field(default=None, max_length=100)
    interests: Optional[CleanList] = None

    @field_validator("avatar_url")
    @classmethod
    def _http_only(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.lower().startswith(("http://", "https://")):
            raise ValueError("avatar_url phải bắt đầu bằng http:// hoặc https://")
        return v or None
