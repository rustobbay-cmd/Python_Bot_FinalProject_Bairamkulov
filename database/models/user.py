"""
Модель пользователя.

Хранит информацию о пользователях бота и их роли.
"""

from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from database.database import Base

if TYPE_CHECKING:
    from .ad import Ad
    from .feedback import Feedback
    from .subscription import Subscription


class User(Base):
    """
    Модель пользователя Telegram.

    Attributes:
        telegram_id: Уникальный ID пользователя в Telegram
        username: Username пользователя (опционально)
        full_name: Полное имя пользователя
        phone: Номер телефона (опционально)
        is_admin: Флаг администратора
        is_banned: Флаг блокировки
        created_at: Дата регистрации
        updated_at: Дата последнего обновления
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="Telegram User ID"
    )
    username: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="Telegram username без @"
    )
    full_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Полное имя пользователя"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Номер телефона"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Является ли администратором"
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Заблокирован ли пользователь"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата регистрации"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления"
    )

    # Relationships
    ads: Mapped[list["Ad"]] = relationship(
        "Ad",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    feedbacks: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, name={self.full_name})>"

    @property
    def mention(self) -> str:
        """Возвращает упоминание пользователя для Telegram."""
        if self.username:
            return f"@{self.username}"
        return f'<a href="tg://user?id={self.telegram_id}">{self.full_name}</a>'

    @property
    def contact_link(self) -> str:
        """Возвращает ссылку для связи с пользователем."""
        if self.username:
            return f"https://t.me/{self.username}"
        return f"tg://user?id={self.telegram_id}"