"""
Конфигурация приложения.

Загружает настройки из переменных окружения с валидацией через Pydantic.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Основные настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Telegram Bot
    bot_token: str = Field(..., description="Токен бота от @BotFather")
    bot_username: str = Field(default="rental_bot", description="Username бота")

    # Database
    db_host: str = Field(default="localhost", description="Хост PostgreSQL")
    db_port: int = Field(default=5432, description="Порт PostgreSQL")
    db_name: str = Field(default="rental_bot", description="Имя базы данных")
    db_user: str = Field(default="postgres", description="Пользователь БД")
    db_password: str = Field(..., description="Пароль БД")

    # Admin
    admin_ids: str = Field(default="", description="ID администраторов через запятую")

    @property
    def database_url(self) -> str:
        """Формирует строку подключения к PostgreSQL."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def admin_id_list(self) -> list[int]:
        """Возвращает список ID администраторов."""
        if not self.admin_ids:
            return []
        return [int(id_.strip()) for id_ in self.admin_ids.split(",") if id_.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Возвращает кэшированный экземпляр настроек.

    Использует lru_cache для однократной загрузки конфигурации.
    """
    return Settings()


# Глобальный доступ к настройкам
settings = get_settings()