"""
Модель объявления об аренде.

Хранит информацию о товарах, выставленных на аренду.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import (
    BigInteger, String, Text, Numeric, Boolean,
    DateTime, ForeignKey, Enum as SQLEnum, func, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from database.database import Base

if TYPE_CHECKING:
    from .user import User
    from .feedback import Feedback
    from .report import Report


class AdStatus(str, Enum):
    """Статусы объявления."""

    PENDING = "pending"  # На модерации
    ACTIVE = "active"  # Активно
    REJECTED = "rejected"  # Отклонено
    RENTED = "rented"  # Сдано в аренду
    CLOSED = "closed"  # Закрыто владельцем


class Ad(Base):
    """
    Модель объявления об аренде.

    Attributes:
        title: Название товара
        description: Описание товара
        price_per_day: Стоимость аренды в день
        location: Местоположение товара
        category: Категория товара
        contact_info: Контактная информация
        photo_id: ID фото в Telegram (опционально)
        status: Статус объявления
        owner_id: ID владельца
        rejection_reason: Причина отклонения (если отклонено)
        views_count: Количество просмотров
    """

    __tablename__ = "ads"

    __table_args__ = (
        Index("ix_ads_search", "title", "description", "location"),
        Index("ix_ads_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Название товара"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Описание товара"
    )
    price_per_day: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Цена за день аренды"
    )
    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Местоположение"
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Категория товара"
    )
    contact_info: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Контактная информация"
    )
    photo_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Telegram File ID фотографии"
    )
    status: Mapped[AdStatus] = mapped_column(
        SQLEnum(AdStatus),
        default=AdStatus.PENDING,
        index=True,
        comment="Статус объявления"
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Причина отклонения"
    )
    views_count: Mapped[int] = mapped_column(
        default=0,
        comment="Количество просмотров"
    )

    # Foreign keys
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="ads",
        lazy="joined"
    )
    feedbacks: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="ad",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="ad",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Ad(id={self.id}, title={self.title}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Проверяет, активно ли объявление."""
        return self.status == AdStatus.ACTIVE

    @property
    def is_pending(self) -> bool:
        """Проверяет, находится ли объявление на модерации."""
        return self.status == AdStatus.PENDING

    @property
    def price_display(self) -> str:
        """Форматированная цена для отображения."""
        return f"{self.price_per_day:,.0f} ₽/день"

    def format_short(self) -> str:
        """Краткое представление объявления."""
        return f"📦 {self.title}\n💰 {self.price_display}\n📍 {self.location}"

    def format_full(self) -> str:
        """Полное представление объявления."""
        status_emoji = {
            AdStatus.PENDING: "⏳",
            AdStatus.ACTIVE: "✅",
            AdStatus.REJECTED: "❌",
            AdStatus.RENTED: "🔒",
            AdStatus.CLOSED: "🚫"
        }

        text = (
            f"{status_emoji.get(self.status, '📦')} <b>{self.title}</b>\n\n"
            f"📝 {self.description}\n\n"
            f"💰 <b>Цена:</b> {self.price_display}\n"
            f"📍 <b>Место:</b> {self.location}\n"
            f"🏷 <b>Категория:</b> {self.category}\n"
            f"📞 <b>Контакт:</b> {self.contact_info}\n"
            f"👁 <b>Просмотров:</b> {self.views_count}"
        )

        if self.status == AdStatus.REJECTED and self.rejection_reason:
            text += f"\n\n❌ <b>Причина отклонения:</b> {self.rejection_reason}"

        return text


# Категории для выбора
AD_CATEGORIES = [
    "🔧 Инструменты",
    "🎮 Электроника",
    "🏠 Для дома",
    "🚗 Транспорт",
    "👗 Одежда",
    "📚 Книги",
    "🎸 Музыка",
    "⚽ Спорт",
    "🎉 Праздники",
    "📦 Другое"
]