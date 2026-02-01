"""
Сервис для работы с объявлениями.

Бизнес-логика создания, поиска и управления объявлениями.
"""

from decimal import Decimal
from sqlalchemy import select, update, delete, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional
from loguru import logger

from database.models import Ad, AdStatus, User


class AdService:
    """Сервис управления объявлениями."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Асинхронная сессия БД
        """
        self.session = session

    async def create(
            self,
            owner_id: int,
            title: str,
            description: str,
            price_per_day: Decimal,
            location: str,
            category: str,
            contact_info: str,
            photo_id: Optional[str] = None
    ) -> Ad:
        """
        Создаёт новое объявление.

        Объявление создаётся со статусом PENDING (на модерации).

        Args:
            owner_id: ID владельца
            title: Название товара
            description: Описание
            price_per_day: Цена за день
            location: Местоположение
            category: Категория
            contact_info: Контактная информация
            photo_id: ID фото в Telegram

        Returns:
            Созданное объявление
        """
        ad = Ad(
            owner_id=owner_id,
            title=title,
            description=description,
            price_per_day=price_per_day,
            location=location,
            category=category,
            contact_info=contact_info,
            photo_id=photo_id,
            status=AdStatus.PENDING
        )

        self.session.add(ad)
        await self.session.commit()
        await self.session.refresh(ad)

        logger.info(f"Created ad #{ad.id}: {title}")
        return ad

    async def get_by_id(self, ad_id: int) -> Optional[Ad]:
        """
        Получает объявление по ID.

        Args:
            ad_id: ID объявления

        Returns:
            Объявление или None
        """
        query = (
            select(Ad)
            .options(selectinload(Ad.owner))
            .where(Ad.id == ad_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_ads(
            self,
            user_id: int,
            status: Optional[AdStatus] = None
    ) -> list[Ad]:
        """
        Получает объявления пользователя.

        Args:
            user_id: ID пользователя
            status: Фильтр по статусу (опционально)

        Returns:
            Список объявлений
        """
        query = (
            select(Ad)
            .where(Ad.owner_id == user_id)
            .order_by(Ad.created_at.desc())
        )

        if status:
            query = query.where(Ad.status == status)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search(
            self,
            keywords: Optional[str] = None,
            location: Optional[str] = None,
            category: Optional[str] = None,
            min_price: Optional[Decimal] = None,
            max_price: Optional[Decimal] = None,
            limit: int = 50,
            offset: int = 0
    ) -> list[Ad]:
        """
        Поиск объявлений по критериям.

        Args:
            keywords: Ключевые слова для поиска
            location: Фильтр по местоположению
            category: Фильтр по категории
            min_price: Минимальная цена
            max_price: Максимальная цена
            limit: Лимит результатов
            offset: Смещение для пагинации

        Returns:
            Список найденных объявлений
        """
        query = (
            select(Ad)
            .options(selectinload(Ad.owner))
            .where(Ad.status == AdStatus.ACTIVE)
            .order_by(Ad.created_at.desc())
        )

        # Поиск по ключевым словам в заголовке и описании
        if keywords:
            search_term = f"%{keywords.lower()}%"
            query = query.where(
                or_(
                    func.lower(Ad.title).like(search_term),
                    func.lower(Ad.description).like(search_term)
                )
            )

        # Фильтр по местоположению
        if location:
            location_term = f"%{location.lower()}%"
            query = query.where(
                func.lower(Ad.location).like(location_term)
            )

        # Фильтр по категории
        if category:
            query = query.where(Ad.category == category)

        # Фильтр по цене
        if min_price is not None:
            query = query.where(Ad.price_per_day >= min_price)
        if max_price is not None:
            query = query.where(Ad.price_per_day <= max_price)

        # Пагинация
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending(self) -> list[Ad]:
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

    async def approve(self, ad_id: int) -> bool:
        """
        Одобряет объявление.

        Args:
            ad_id: ID объявления

        Returns:
            True если успешно
        """
        query = (
            update(Ad)
            .where(Ad.id == ad_id)
            .where(Ad.status == AdStatus.PENDING)
            .values(status=AdStatus.ACTIVE)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        if result.rowcount > 0:
            logger.info(f"Ad #{ad_id} approved")
            return True
        return False

    async def reject(self, ad_id: int, reason: str) -> bool:
        """
        Отклоняет объявление.

        Args:
            ad_id: ID объявления
            reason: Причина отклонения

        Returns:
            True если успешно
        """
        query = (
            update(Ad)
            .where(Ad.id == ad_id)
            .where(Ad.status == AdStatus.PENDING)
            .values(status=AdStatus.REJECTED, rejection_reason=reason)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        if result.rowcount > 0:
            logger.info(f"Ad #{ad_id} rejected: {reason}")
            return True
        return False

    async def update_ad(
            self,
            ad_id: int,
            owner_id: int,
            **fields
    ) -> bool:
        """
        Обновляет поля объявления.

        После редактирования объявление снова отправляется на модерацию.

        Args:
            ad_id: ID объявления
            owner_id: ID владельца (для проверки прав)
            **fields: Поля для обновления

        Returns:
            True если успешно
        """
        # Проверяем, что объявление принадлежит пользователю
        ad = await self.get_by_id(ad_id)
        if not ad or ad.owner_id != owner_id:
            return False

        # Фильтруем только допустимые поля
        allowed_fields = {
            'title', 'description', 'price_per_day',
            'location', 'category', 'contact_info', 'photo_id'
        }
        update_data = {k: v for k, v in fields.items() if k in allowed_fields}

        if not update_data:
            return False

        # После редактирования - на модерацию
        update_data['status'] = AdStatus.PENDING
        update_data['rejection_reason'] = None

        query = (
            update(Ad)
            .where(Ad.id == ad_id)
            .values(**update_data)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        if result.rowcount > 0:
            logger.info(f"Ad #{ad_id} updated, sent to moderation")
            return True
        return False

    async def set_status(self, ad_id: int, owner_id: int, status: AdStatus) -> bool:
        """
        Устанавливает статус объявления владельцем.

        Args:
            ad_id: ID объявления
            owner_id: ID владельца
            status: Новый статус (RENTED или CLOSED)

        Returns:
            True если успешно
        """
        allowed_statuses = {AdStatus.RENTED, AdStatus.CLOSED}
        if status not in allowed_statuses:
            return False

        query = (
            update(Ad)
            .where(Ad.id == ad_id)
            .where(Ad.owner_id == owner_id)
            .where(Ad.status == AdStatus.ACTIVE)
            .values(status=status)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0

    async def reactivate(self, ad_id: int, owner_id: int) -> bool:
        """
        Возвращает объявление в активный статус.

        Args:
            ad_id: ID объявления
            owner_id: ID владельца

        Returns:
            True если успешно
        """
        query = (
            update(Ad)
            .where(Ad.id == ad_id)
            .where(Ad.owner_id == owner_id)
            .where(Ad.status.in_([AdStatus.RENTED, AdStatus.CLOSED]))
            .values(status=AdStatus.ACTIVE)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0

    async def delete_ad(self, ad_id: int, owner_id: int) -> bool:
        """
        Удаляет объявление.

        Args:
            ad_id: ID объявления
            owner_id: ID владельца

        Returns:
            True если успешно
        """
        query = (
            delete(Ad)
            .where(Ad.id == ad_id)
            .where(Ad.owner_id == owner_id)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        if result.rowcount > 0:
            logger.info(f"Ad #{ad_id} deleted by owner {owner_id}")
            return True
        return False

    async def increment_views(self, ad_id: int) -> None:
        """
        Увеличивает счётчик просмотров.

        Args:
            ad_id: ID объявления
        """
        query = (
            update(Ad)
            .where(Ad.id == ad_id)
            .values(views_count=Ad.views_count + 1)
        )
        await self.session.execute(query)
        await self.session.commit()

    async def get_stats(self) -> dict:
        """
        Получает статистику по объявлениям.

        Returns:
            Словарь со статистикой
        """
        total_query = select(func.count(Ad.id))
        total = await self.session.execute(total_query)

        active_query = select(func.count(Ad.id)).where(Ad.status == AdStatus.ACTIVE)
        active = await self.session.execute(active_query)

        pending_query = select(func.count(Ad.id)).where(Ad.status == AdStatus.PENDING)
        pending = await self.session.execute(pending_query)

        return {
            'total': total.scalar_one(),
            'active': active.scalar_one(),
            'pending': pending.scalar_one()
        }