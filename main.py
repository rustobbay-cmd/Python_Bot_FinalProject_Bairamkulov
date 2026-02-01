"""
Telegram бот для аренды вещей.

Точка входа приложения. Инициализация и запуск бота.
"""

import asyncio
import sys
from loguru import logger

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import db
from bot.handlers import get_all_routers
from bot.middlewares import DatabaseMiddleware, ThrottlingMiddleware


def setup_logging() -> None:
    """Настройка логирования."""
    logger.remove()  # Удаляем стандартный handler

    # Формат логов
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Консольный вывод
    logger.add(
        sys.stdout,
        format=log_format,
        level="INFO",
        colorize=True
    )

    # Файловый лог
    logger.add(
        "logs/bot_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="00:00",  # Новый файл каждый день
        retention="7 days",  # Хранить 7 дней
        compression="zip"
    )


async def on_startup(bot: Bot) -> None:
    """Действия при запуске бота."""
    logger.info("Бот запускается...")

    # Создаём таблицы в БД
    await db.create_tables()
    logger.info("База данных инициализирована")

    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"Бот @{bot_info.username} успешно запущен!")


async def on_shutdown(bot: Bot) -> None:
    """Действия при остановке бота."""
    logger.info("Бот останавливается...")

    # Закрываем соединение с БД
    await db.close()
    logger.info("Соединение с базой данных закрыто")


def create_bot() -> Bot:
    """Создание экземпляра бота."""
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )


def create_dispatcher() -> Dispatcher:
    """Создание и настройка диспетчера."""
    # Используем MemoryStorage для FSM
    # В продакшене лучше Redis: RedisStorage.from_url(...)
    storage = MemoryStorage()

    dp = Dispatcher(storage=storage)

    # Регистрируем middleware
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.3))
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())

    # Регистрируем роутеры
    for router in get_all_routers():
        dp.include_router(router)
        logger.debug(f"Зарегистрирован роутер: {router.name}")

    # Регистрируем события запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    return dp


async def main() -> None:
    """Главная функция запуска бота."""
    setup_logging()

    logger.info("=" * 50)
    logger.info("RENTAL BOT - Бот аренды вещей")
    logger.info("=" * 50)

    bot = create_bot()
    dp = create_dispatcher()

    try:
        # Удаляем старые webhook (если были)
        await bot.delete_webhook(drop_pending_updates=True)

        # Запускаем long polling
        logger.info("Запуск в режиме long polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )

    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Необработанное исключение: {e}")
        sys.exit(1)