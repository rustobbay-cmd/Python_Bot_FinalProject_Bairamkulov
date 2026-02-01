"""
Middleware для работы с базой данных.

Внедряет сессию БД и сервисы в обработчики.
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database import db
from services import UserService, AdService, ModerationService
from services.notification_service import SubscriptionService


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для внедрения сессии базы данных.

    Создаёт сессию для каждого запроса и закрывает её после обработки.
    Также автоматически создаёт/обновляет пользователя.
    """

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
        Обработка события с внедрением сессии БД.

        Args:
            handler: Следующий обработчик
            event: Событие Telegram
            data: Данные контекста
        """
        async with db.session_factory() as session:
            # Внедряем сессию
            data["session"] = session

            # Создаём сервисы
            user_service = UserService(session)
            ad_service = AdService(session)
            moderation_service = ModerationService(session)
            subscription_service = SubscriptionService(session)

            data["user_service"] = user_service
            data["ad_service"] = ad_service
            data["moderation_service"] = moderation_service
            data["subscription_service"] = subscription_service

            # Получаем или создаём пользователя
            user = None
            if isinstance(event, (Message, CallbackQuery)):
                tg_user = event.from_user
                if tg_user:
                    user, created = await user_service.get_or_create(
                        telegram_id=tg_user.id,
                        username=tg_user.username,
                        full_name=tg_user.full_name
                    )
                    data["db_user"] = user

            # Проверяем бан
            if user and user.is_banned:
                if isinstance(event, Message):
                    await event.answer(
                        "⛔ Вы заблокированы и не можете использовать бота.\n"
                        "Если считаете это ошибкой, свяжитесь с администрацией."
                    )
                    return
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "⛔ Вы заблокированы",
                        show_alert=True
                    )
                    return

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов.

    Предотвращает спам и DoS-атаки.
    """

    def __init__(self, rate_limit: float = 0.5):
        """
        Инициализация middleware.

        Args:
            rate_limit: Минимальный интервал между запросами в секундах
        """
        self.rate_limit = rate_limit
        self.user_last_request: Dict[int, float] = {}

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
        Проверяет частоту запросов.

        Args:
            handler: Следующий обработчик
            event: Событие Telegram
            data: Данные контекста
        """
        import time

        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id if event.from_user else None

        if user_id:
            current_time = time.time()
            last_request = self.user_last_request.get(user_id, 0)

            if current_time - last_request < self.rate_limit:
                # Слишком частые запросы
                if isinstance(event, CallbackQuery):
                    await event.answer(
                        "⏳ Подождите немного...",
                        show_alert=False
                    )
                return

            self.user_last_request[user_id] = current_time

        return await handler(event, data)