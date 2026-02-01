"""
Вспомогательные функции.

Утилиты общего назначения.
"""

import hashlib
from typing import Any, TypeVar, Sequence
from functools import wraps
import asyncio
from loguru import logger

T = TypeVar('T')


def chunks(lst: Sequence[T], n: int):
    """
    Разбивает список на чанки заданного размера.

    Args:
        lst: Исходный список
        n: Размер чанка

    Yields:
        Чанки списка
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def generate_callback_id(prefix: str, *args: Any) -> str:
    """
    Генерирует уникальный ID для callback_data.

    Args:
        prefix: Префикс callback
        args: Дополнительные аргументы

    Returns:
        Строка callback_data (макс 64 символа)
    """
    parts = [prefix] + [str(arg) for arg in args]
    return ":".join(parts)[:64]


def parse_callback_id(callback_data: str) -> tuple[str, list[str]]:
    """
    Парсит callback_data на префикс и аргументы.

    Args:
        callback_data: Строка callback_data

    Returns:
        Кортеж (префикс, [аргументы])
    """
    parts = callback_data.split(":")
    return parts[0], parts[1:] if len(parts) > 1 else []


def make_hash(data: str) -> str:
    """
    Создаёт короткий хэш строки.

    Args:
        data: Исходная строка

    Returns:
        8-символьный хэш
    """
    return hashlib.md5(data.encode()).hexdigest()[:8]


def retry_async(
        retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,)
):
    """
    Декоратор для повторных попыток асинхронных функций.

    Args:
        retries: Количество попыток
        delay: Начальная задержка между попытками
        backoff: Множитель задержки
        exceptions: Исключения для перехвата
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {retries} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


def safe_int(value: Any, default: int = 0) -> int:
    """
    Безопасное преобразование в int.

    Args:
        value: Значение для преобразования
        default: Значение по умолчанию

    Returns:
        int значение или default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Безопасное преобразование в float.

    Args:
        value: Значение для преобразования
        default: Значение по умолчанию

    Returns:
        float значение или default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def build_menu(
        buttons: list,
        n_cols: int = 2,
        header_buttons: list = None,
        footer_buttons: list = None
) -> list:
    """
    Строит меню из кнопок с заданным количеством колонок.

    Args:
        buttons: Список кнопок
        n_cols: Количество колонок
        header_buttons: Кнопки в начале (на всю ширину)
        footer_buttons: Кнопки в конце (на всю ширину)

    Returns:
        Список рядов кнопок
    """
    menu = []

    if header_buttons:
        menu.extend([[btn] for btn in header_buttons])

    menu.extend([list(row) for row in chunks(buttons, n_cols)])

    if footer_buttons:
        menu.extend([[btn] for btn in footer_buttons])

    return menu


def clean_text_for_search(text: str) -> str:
    """
    Очищает текст для поискового запроса.

    Args:
        text: Исходный текст

    Returns:
        Очищенный текст
    """
    # Приводим к нижнему регистру
    text = text.lower()

    # Убираем лишние пробелы
    text = ' '.join(text.split())

    # Убираем специальные символы
    import re
    text = re.sub(r'[^\w\s]', '', text)

    return text