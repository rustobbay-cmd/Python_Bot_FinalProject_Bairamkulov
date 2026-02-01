"""
Сервис для работы с пользователями.

Бизнес-логика управления пользователями.
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from loguru import logger

from database.models import User
from config import settings


class UserService:
    """Сервис управления пользователями."""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            session: Асинхронная сессия БД
        """
        self.session = session

    async def get_or_create(
            self,
            telegram_id: int,
            username: Optional[str] = None,
            full_name: str = "Пользователь"
    ) -> tuple[User, bool]:
        """
        Получает или создаёт пользователя.

        Args:
            telegram_id: Telegram ID пользователя
            username: Username пользователя
            full_name: Полное имя

        Returns:
            Кортеж (пользователь, был_ли_создан)
        """
        # Пытаемся найти существующего
        user = await self.get_by_telegram_id(telegram_id)

        if user:
            # Обновляем данные если изменились
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                updated = True

            if updated:
                await self.session.commit()
                logger.debug(f"Updated user {telegram_id}")

            return user, False

        # Создаём нового
        is_admin = telegram_id in settings.admin_id_list

        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            is_admin=is_admin
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info(f"Created new user: {telegram_id} ({full_name})")
        return user, True

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получает пользователя по Telegram ID.

        Args:
            telegram_id: Telegram ID

        Returns:
            Пользователь или None
        """
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя по внутреннему ID.

        Args:
            user_id: ID пользователя в БД

        Returns:
            Пользователь или None
        """
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_phone(self, user_id: int, phone: str) -> bool:
        """
        Обновляет номер телефона пользователя.

        Args:
            user_id: ID пользователя
            phone: Новый номер телефона

        Returns:
            True если успешно
        """
        query = (
            update(User)
            .where(User.id == user_id)
            .values(phone=phone)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0

    async def ban_user(self, user_id: int, ban: bool = True) -> bool:
        """
        Блокирует/разблокирует пользователя.

        Args:
            user_id: ID пользователя
            ban: True для блокировки, False для разблокировки

        Returns:
            True если успешно
        """
        query = (
            update(User)
            .where(User.id == user_id)
            .values(is_banned=ban)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        action = "banned" if ban else "unbanned"
        logger.info(f"User {user_id} {action}")

        return result.rowcount > 0

    async def set_admin(self, user_id: int, is_admin: bool = True) -> bool:
        """
        Устанавливает/снимает права администратора.

        Args:
            user_id: ID пользователя
            is_admin: True для назначения, False для снятия

        Returns:
            True если успешно
        """
        query = (
            update(User)
            .where(User.id == user_id)
            .values(is_admin=is_admin)
        )
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0

    async def get_all_admins(self) -> list[User]:
        """
        Получает список всех администраторов.

        Returns:
            Список пользователей-администраторов
        """
        query = select(User).where(User.is_admin == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_users_count(self) -> int:
        """
        Получает общее количество пользователей.

        Returns:
            Количество пользователей
        """
        from sqlalchemy import func
        query = select(func.count(User.id))
        result = await self.session.execute(query)
        return result.scalar_one()

    async def is_banned(self, telegram_id: int) -> bool:
        """
        Проверяет, заблокирован ли пользователь.

        Args:
            telegram_id: Telegram ID

        Returns:
            True если заблокирован
        """
        user = await self.get_by_telegram_id(telegram_id)
        return user.is_banned if user else False