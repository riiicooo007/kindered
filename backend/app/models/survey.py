from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow


class SurveyAnswer(Base):
    __tablename__ = "survey_answers"
    __table_args__ = (UniqueConstraint("user_id", name="uq_survey_answers_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    age_group: Mapped[str] = mapped_column(String(50))
    situation: Mapped[str] = mapped_column(String(100))
    recent_feeling: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    goals: Mapped[list] = mapped_column(JSON, default=list)
    topics: Mapped[list] = mapped_column(JSON, default=list)
    activities: Mapped[list] = mapped_column(JSON, default=list)
    chat_style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    story: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="survey")
