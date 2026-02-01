"""
Модуль подключения к базе данных.

Реализует асинхронное подключение к PostgreSQL через SQLAlchemy 2.0.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from loguru import logger

from config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""
    pass


class Database:
    """
    Менеджер подключения к базе данных.

    Управляет созданием engine и сессий для асинхронной работы с PostgreSQL.
    """

    def __init__(self, url: str):
        """
        Инициализация подключения.

        Args:
            url: Строка подключения к PostgreSQL
        """
        self._engine: AsyncEngine = create_async_engine(
            url,
            echo=False,  # Установить True для отладки SQL-запросов
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )

    @property
    def engine(self) -> AsyncEngine:
        """Возвращает engine базы данных."""
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Возвращает фабрику сессий."""
        return self._session_factory

    async def create_tables(self) -> None:
        """
        Создаёт все таблицы в базе данных.

        Использует metadata из Base для создания схемы.
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы базы данных созданы")

    async def drop_tables(self) -> None:
        """Удаляет все таблицы из базы данных."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Все таблицы удалены")

    async def close(self) -> None:
        """Закрывает соединение с базой данных."""
        await self._engine.dispose()
        logger.info("Соединение с базой данных закрыто")


# Глобальный экземпляр базы данных
db = Database(settings.database_url)


async def get_session() -> AsyncSession:
    """
    Генератор сессий для dependency injection.

    Yields:
        AsyncSession: Асинхронная сессия базы данных
    """
    async with db.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise