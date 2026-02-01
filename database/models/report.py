"""
Модель жалоб на объявления.

Позволяет пользователям сообщать о нарушениях.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Text, DateTime, ForeignKey,
    Enum as SQLEnum, func, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from database.database import Base

if TYPE_CHECKING:
    from .user import User
    from .ad import Ad


class ReportReason(str, Enum):
    """Причины жалобы."""

    SPAM = "spam"  # Спам
    FRAUD = "fraud"  # Мошенничество
    INAPPROPRIATE = "inappropriate"  # Неприемлемый контент
    WRONG_CATEGORY = "wrong_category"  # Неверная категория
    FAKE = "fake"  # Фейковое объявление
    OTHER = "other"  # Другое


class ReportStatus(str, Enum):
    """Статус рассмотрения жалобы."""

    PENDING = "pending"  # Ожидает рассмотрения
    REVIEWED = "reviewed"  # Рассмотрено
    DISMISSED = "dismissed"  # Отклонено


class Report(Base):
    """
    Модель жалобы на объявление.

    Attributes:
        reason: Причина жалобы
        description: Описание нарушения
        status: Статус рассмотрения
        reporter_id: ID пользователя, подавшего жалобу
        ad_id: ID объявления
        reviewed_by: ID модератора, рассмотревшего жалобу
        admin_comment: Комментарий модератора
    """

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reason: Mapped[ReportReason] = mapped_column(
        SQLEnum(ReportReason),
        nullable=False,
        comment="Причина жалобы"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Подробное описание"
    )
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus),
        default=ReportStatus.PENDING,
        index=True,
        comment="Статус жалобы"
    )
    admin_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Комментарий модератора"
    )

    # Foreign keys
    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ad_id: Mapped[int] = mapped_column(
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    reporter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reporter_id],
        lazy="joined"
    )
    ad: Mapped["Ad"] = relationship(
        "Ad",
        back_populates="reports",
        lazy="joined"
    )
    reviewer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[reviewed_by],
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, reason={self.reason}, status={self.status})>"

    @property
    def reason_display(self) -> str:
        """Человекочитаемая причина жалобы."""
        reasons = {
            ReportReason.SPAM: "🚫 Спам",
            ReportReason.FRAUD: "⚠️ Мошенничество",
            ReportReason.INAPPROPRIATE: "🔞 Неприемлемый контент",
            ReportReason.WRONG_CATEGORY: "📁 Неверная категория",
            ReportReason.FAKE: "🎭 Фейковое объявление",
            ReportReason.OTHER: "❓ Другое"
        }
        return reasons.get(self.reason, str(self.reason))

    def format_for_admin(self) -> str:
        """Форматирование жалобы для администратора."""
        text = (
            f"🚨 <b>Жалоба #{self.id}</b>\n\n"
            f"📋 <b>Причина:</b> {self.reason_display}\n"
            f"📝 <b>Описание:</b> {self.description or 'Не указано'}\n\n"
            f"📦 <b>Объявление:</b> {self.ad.title}\n"
            f"👤 <b>Автор жалобы:</b> {self.reporter.full_name}\n"
            f"📅 <b>Дата:</b> {self.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        return text


# Отображение причин для клавиатуры
REPORT_REASONS_DISPLAY = {
    ReportReason.SPAM: "🚫 Спам",
    ReportReason.FRAUD: "⚠️ Мошенничество",
    ReportReason.INAPPROPRIATE: "🔞 Неприемлемый контент",
    ReportReason.WRONG_CATEGORY: "📁 Неверная категория",
    ReportReason.FAKE: "🎭 Фейковое объявление",
    ReportReason.OTHER: "❓ Другое"
}