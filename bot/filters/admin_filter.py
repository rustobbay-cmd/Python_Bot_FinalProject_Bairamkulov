"""
Фильтры для проверки прав доступа.

Кастомные фильтры aiogram для проверки администраторов и других условий.
"""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Union

from config import settings


class IsAdminFilter(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь администратором.

    Использование:
        @router.message(IsAdminFilter())
        async def admin_handler(message: Message):
            ...
    """

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        """
        Проверяет, является ли отправитель администратором.

        Args:
            event: Сообщение или callback query

        Returns:
            True если пользователь админ
        """
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return False

        return user_id in settings.admin_id_list


class IsNotBannedFilter(BaseFilter):
    """
    Фильтр для проверки, что пользователь не заблокирован.

    Требует передачи сессии БД через middleware.
    """

    async def __call__(
            self,
            event: Union[Message, CallbackQuery],
            user_service=None
    ) -> bool:
        """
        Проверяет, не заблокирован ли пользователь.

        Args:
            event: Сообщение или callback query
            user_service: Сервис пользователей (из middleware)

        Returns:
            True если пользователь НЕ заблокирован
        """
        if user_service is None:
            # Если сервис не передан, пропускаем
            return True

        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return True

        return not await user_service.is_banned(user_id)


class IsPrivateChatFilter(BaseFilter):
    """Фильтр для проверки, что сообщение из личного чата."""

    async def __call__(self, message: Message) -> bool:
        """
        Проверяет тип чата.

        Args:
            message: Сообщение

        Returns:
            True если личный чат
        """
        return message.chat.type == "private"


class HasContactFilter(BaseFilter):
    """Фильтр для проверки наличия контакта в сообщении."""

    async def __call__(self, message: Message) -> bool:
        """
        Проверяет наличие контакта.

        Args:
            message: Сообщение

        Returns:
            True если есть контакт
        """
        return message.contact is not None


class HasPhotoFilter(BaseFilter):
    """Фильтр для проверки наличия фото в сообщении."""

    async def __call__(self, message: Message) -> bool:
        """
        Проверяет наличие фото.

        Args:
            message: Сообщение

        Returns:
            True если есть фото
        """
        return message.photo is not None and len(message.photo) > 0