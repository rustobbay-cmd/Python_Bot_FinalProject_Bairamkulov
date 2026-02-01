"""
Сервис модерации.

Бизнес-логика модерации объявлений и обработки жалоб.
"""

from datetime import datetime
from sqlalchemy import select, update as sql_update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional
from loguru import logger

from database.models import (
    Ad, AdStatus, Report, ReportReason, ReportStatus, User
)


class ModerationService:
    """Сервис модерации объявлений."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Асинхронная сессия БД
        """
        self.session = session

    async def get_pending_ads(self) -> list[Ad]:
        """
        Получает объявления, ожидающие модерации.

        Returns:
            Список объявлений на модерации
        """
        query = (
            select(Ad)
            .options(selectinload(Ad.owner))
            .where(Ad.status == AdStatus.PENDING)
            .order_by(Ad.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_count(self) -> int:
        """
        Получает количество объявлений на модерации.

        Returns:
            Количество объявлений
        """
        query = (
            select(func.count(Ad.id))
            .where(Ad.status == AdStatus.PENDING)
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def approve_ad(self, ad_id: int, moderator_id: int) -> Optional[Ad]:
        """
        Одобряет объявление.

        Args:
            ad_id: ID объявления
            moderator_id: ID модератора

        Returns:
            Одобренное объявление или None
        """
        # Получаем объявление
        query = (
            select(Ad)
            .options(selectinload(Ad.owner))
            .where(Ad.id == ad_id)
            .where(Ad.status == AdStatus.PENDING)
        )
        result = await self.session.execute(query)
        ad = result.scalar_one_or_none()

        if not ad:
            return None

        # Обновляем статус
        ad.status = AdStatus.ACTIVE
        await self.session.commit()

        logger.info(f"Ad #{ad_id} approved by moderator {moderator_id}")
        return ad

    async def reject_ad(
            self,
            ad_id: int,
            moderator_id: int,
            reason: str
    ) -> Optional[Ad]:
        """
        Отклоняет объявление.

        Args:
            ad_id: ID объявления
            moderator_id: ID модератора
            reason: Причина отклонения

        Returns:
            Отклонённое объявление или None
        """
        query = (
            select(Ad)
            .options(selectinload(Ad.owner))
            .where(Ad.id == ad_id)
            .where(Ad.status == AdStatus.PENDING)
        )
        result = await self.session.execute(query)
        ad = result.scalar_one_or_none()

        if not ad:
            return None

        ad.status = AdStatus.REJECTED
        ad.rejection_reason = reason
        await self.session.commit()

        logger.info(f"Ad #{ad_id} rejected by moderator {moderator_id}: {reason}")
        return ad

    async def create_report(
            self,
            ad_id: int,
            reporter_id: int,
            reason: ReportReason,
            description: Optional[str] = None
    ) -> Report:
        """
        Создаёт жалобу на объявление.

        Args:
            ad_id: ID объявления
            reporter_id: ID пользователя
            reason: Причина жалобы
            description: Описание

        Returns:
            Созданная жалоба
        """
        report = Report(
            ad_id=ad_id,
            reporter_id=reporter_id,
            reason=reason,
            description=description,
            status=ReportStatus.PENDING
        )

        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)

        logger.info(f"Created report #{report.id} for ad #{ad_id}")
        return report

    async def get_pending_reports(self) -> list[Report]:
        """
        Получает нерассмотренные жалобы.

        Returns:
            Список жалоб
        """
        query = (
            select(Report)
            .options(
                selectinload(Report.ad),
                selectinload(Report.reporter)
            )
            .where(Report.status == ReportStatus.PENDING)
            .order_by(Report.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_reports_count(self) -> int:
        """Получает количество нерассмотренных жалоб."""
        query = (
            select(func.count(Report.id))
            .where(Report.status == ReportStatus.PENDING)
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def review_report(
            self,
            report_id: int,
            moderator_id: int,
            action: str,
            comment: Optional[str] = None
    ) -> Optional[Report]:
        """
        Рассматривает жалобу.

        Args:
            report_id: ID жалобы
            moderator_id: ID модератора
            action: Действие ('approve' - удалить объявление, 'dismiss' - отклонить жалобу)
            comment: Комментарий модератора

        Returns:
            Обработанная жалоба или None
        """
        query = (
            select(Report)
            .options(selectinload(Report.ad))
            .where(Report.id == report_id)
            .where(Report.status == ReportStatus.PENDING)
        )
        result = await self.session.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            return None

        report.reviewed_by = moderator_id
        report.reviewed_at = datetime.now()
        report.admin_comment = comment

        if action == 'approve':
            # Удаляем/скрываем объявление
            report.status = ReportStatus.REVIEWED
            if report.ad:
                report.ad.status = AdStatus.CLOSED
            logger.info(f"Report #{report_id} approved, ad closed")
        else:
            # Отклоняем жалобу
            report.status = ReportStatus.DISMISSED
            logger.info(f"Report #{report_id} dismissed")

        await self.session.commit()
        return report

    async def get_ad_reports(self, ad_id: int) -> list[Report]:
        """
        Получает все жалобы на объявление.

        Args:
            ad_id: ID объявления

        Returns:
            Список жалоб
        """
        query = (
            select(Report)
            .options(selectinload(Report.reporter))
            .where(Report.ad_id == ad_id)
            .order_by(Report.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_moderation_stats(self) -> dict:
        """
        Получает статистику модерации.

        Returns:
            Словарь со статистикой
        """
        # Объявления
        pending_ads = await self.get_pending_count()

        # Жалобы
        pending_reports = await self.get_pending_reports_count()

        # Всего за сегодня
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        approved_today_query = (
            select(func.count(Ad.id))
            .where(Ad.status == AdStatus.ACTIVE)
            .where(Ad.updated_at >= today_start)
        )
        approved_today = (await self.session.execute(approved_today_query)).scalar_one()

        return {
            'pending_ads': pending_ads,
            'pending_reports': pending_reports,
            'approved_today': approved_today
        }