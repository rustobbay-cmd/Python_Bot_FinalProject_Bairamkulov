"""
Модель подписок на уведомления.

Позволяет пользователям получать уведомления о новых объявлениях
по заданным критериям.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, DateTime,
    ForeignKey, Boolean, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from database.database import Base

if TYPE_CHECKING:
    from .user import User


class Subscription(Base):
    """
    Модель подписки на уведомления.

    Пользователь может подписаться на объявления по:
    - Ключевым словам
    - Категории
    - Местоположению
    - Диапазону цен

    Attributes:
        keywords: Ключевые слова для поиска
        category: Категория товаров
        location: Местоположение
        max_price: Максимальная цена
        is_active: Активна ли подписка
        user_id: ID пользователя
    """

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    keywords: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Ключевые слова для поиска"
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Категория товаров"
    )
    location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
        comment="Местоположение"
    )
    max_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Максимальная цена"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Активна ли подписка"
    )

    # Foreign key
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="subscriptions",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

    def matches_ad(self, ad) -> bool:
        """
        Проверяет, соответствует ли объявление критериям подписки.

        Args:
            ad: Объект объявления для проверки

        Returns:
            True если объявление соответствует критериям
        """
        # Проверка ключевых слов
        if self.keywords:
            keywords_lower = self.keywords.lower()
            title_lower = ad.title.lower()
            desc_lower = ad.description.lower()

            if keywords_lower not in title_lower and keywords_lower not in desc_lower:
                return False

        # Проверка категории
        if self.category and self.category != ad.category:
            return False

        # Проверка местоположения
        if self.location:
            if self.location.lower() not in ad.location.lower():
                return False

        # Проверка максимальной цены
        if self.max_price and ad.price_per_day > self.max_price:
            return False

        return True

    def format_display(self) -> str:
        """Форматированное отображение подписки."""
        status = "✅ Активна" if self.is_active else "⏸ Приостановлена"

        parts = [f"🔔 <b>Подписка #{self.id}</b> ({status})"]

        if self.keywords:
            parts.append(f"🔍 Ключевые слова: {self.keywords}")
        if self.category:
            parts.append(f"🏷 Категория: {self.category}")
        if self.location:
            parts.append(f"📍 Место: {self.location}")
        if self.max_price:
            parts.append(f"💰 Макс. цена: {self.max_price:,.0f} ₽/день")

        if len(parts) == 1:
            parts.append("📭 Критерии не заданы (все объявления)")

        return "\n".join(parts)