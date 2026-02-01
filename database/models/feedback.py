"""
Модель отзывов.

Хранит отзывы пользователей о товарах и о работе бота.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    String, Text, Integer, DateTime,
    ForeignKey, Enum as SQLEnum, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from database.database import Base

if TYPE_CHECKING:
    from .user import User
    from .ad import Ad


class FeedbackType(str, Enum):
    """Типы отзывов."""

    AD = "ad"  # Отзыв о товаре/объявлении
    BOT = "bot"  # Отзыв о работе бота
    OWNER = "owner"  # Отзыв о владельце товара


class Feedback(Base):
    """
    Модель отзыва.

    Attributes:
        feedback_type: Тип отзыва (о товаре, боте или владельце)
        rating: Оценка от 1 до 5
        text: Текст отзыва
        user_id: ID автора отзыва
        ad_id: ID объявления (если отзыв о товаре)
    """

    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    feedback_type: Mapped[FeedbackType] = mapped_column(
        SQLEnum(FeedbackType),
        nullable=False,
        index=True,
        comment="Тип отзыва"
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Оценка от 1 до 5"
    )
    text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Текст отзыва"
    )

    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ad_id: Mapped[int | None] = mapped_column(
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="feedbacks",
        lazy="joined"
    )
    ad: Mapped["Ad | None"] = relationship(
        "Ad",
        back_populates="feedbacks",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, type={self.feedback_type}, rating={self.rating})>"

    @property
    def rating_stars(self) -> str:
        """Возвращает оценку в виде звёзд."""
        return "⭐" * self.rating + "☆" * (5 - self.rating)

    def format_display(self) -> str:
        """Форматированный вывод отзыва."""
        text = f"{self.rating_stars}\n"

        if self.text:
            text += f"💬 {self.text}\n"

        text += f"\n👤 {self.user.full_name}"
        text += f"\n📅 {self.created_at.strftime('%d.%m.%Y')}"

        return text