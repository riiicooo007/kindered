from pydantic import BaseModel, Field

from app.schemas.user import PublicUser


class MatchResult(BaseModel):
    user: PublicUser
    score: float = Field(description="Điểm tương đồng 0-100")
    common_interests: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
