from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import CleanList, UTCDatetime


class SurveyIn(BaseModel):
    age_group: str = Field(min_length=1, max_length=50)
    situation: str = Field(min_length=1, max_length=100)
    recent_feeling: Optional[str] = Field(default=None, max_length=100)
    goals: CleanList = Field(default_factory=list)
    topics: CleanList = Field(default_factory=list)
    activities: CleanList = Field(default_factory=list)
    chat_style: Optional[str] = Field(default=None, max_length=100)
    story: Optional[str] = Field(default=None, max_length=2000)


class SurveyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    age_group: str
    situation: str
    recent_feeling: Optional[str] = None
    goals: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)
    chat_style: Optional[str] = None
    story: Optional[str] = None
    updated_at: UTCDatetime
