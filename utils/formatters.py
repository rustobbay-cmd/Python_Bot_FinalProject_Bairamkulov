"""
Форматтеры для отображения данных.

Форматирование сообщений, цен, дат и других данных.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional


def format_price(price: Decimal, with_currency: bool = True) -> str:
    """
    Форматирует цену для отображения.

    Args:
        price: Цена в Decimal
        with_currency: Добавлять ли символ валюты

    Returns:
        Форматированная строка цены
    """
    # Форматируем с разделителями тысяч
    formatted = f"{price:,.0f}".replace(",", " ")

    if with_currency:
        return f"{formatted} ₽"
    return formatted


def format_phone_clickable(phone: str) -> str:
    """
    Форматирует телефон как кликабельную ссылку.

    Args:
        phone: Номер телефона

    Returns:
        HTML-ссылка для звонка
    """
    # Убираем пробелы и скобки для ссылки
    clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    return f'<a href="tel:{clean_phone}">{phone}</a>'


def format_datetime(dt: datetime, include_time: bool = True) -> str:
    """
    Форматирует дату и время по-русски.

    Args:
        dt: Объект datetime
        include_time: Включать ли время

    Returns:
        Форматированная строка
    """
    months = [
        "", "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]

    date_str = f"{dt.day} {months[dt.month]} {dt.year}"

    if include_time:
        return f"{date_str} в {dt.strftime('%H:%M')}"
    return date_str


def format_datetime_short(dt: datetime) -> str:
    """
    Короткий формат даты и времени.

    Args:
        dt: Объект datetime

    Returns:
        Строка формата DD.MM.YY HH:MM
    """
    return dt.strftime("%d.%m.%y %H:%M")


def format_relative_time(dt: datetime) -> str:
    """
    Форматирует время относительно текущего момента.

    Args:
        dt: Объект datetime

    Returns:
        Строка вида "5 минут назад", "вчера" и т.д.
    """
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "только что"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} {_pluralize(minutes, 'минуту', 'минуты', 'минут')} назад"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} {_pluralize(hours, 'час', 'часа', 'часов')} назад"
    elif seconds < 172800:
        return "вчера"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} {_pluralize(days, 'день', 'дня', 'дней')} назад"
    else:
        return format_datetime(dt, include_time=False)


def _pluralize(n: int, one: str, few: str, many: str) -> str:
    """
    Склонение слов в зависимости от числа.

    Args:
        n: Число
        one: Форма для 1 (день)
        few: Форма для 2-4 (дня)
        many: Форма для 5+ (дней)

    Returns:
        Правильная форма слова
    """
    if 11 <= n % 100 <= 19:
        return many
    elif n % 10 == 1:
        return one
    elif 2 <= n % 10 <= 4:
        return few
    else:
        return many


def format_ad_list(ads: list, page: int = 1, per_page: int = 5) -> str:
    """
    Форматирует список объявлений для отображения.

    Args:
        ads: Список объявлений
        page: Номер страницы
        per_page: Количество на странице

    Returns:
        Форматированный текст
    """
    if not ads:
        return "📭 Объявления не найдены"

    start = (page - 1) * per_page
    end = start + per_page
    page_ads = ads[start:end]

    lines = [f"📋 <b>Найдено объявлений: {len(ads)}</b>\n"]

    for i, ad in enumerate(page_ads, start=start + 1):
        lines.append(f"{i}. {ad.format_short()}\n")

    total_pages = (len(ads) + per_page - 1) // per_page
    if total_pages > 1:
        lines.append(f"\n📄 Страница {page} из {total_pages}")

    return "\n".join(lines)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезает текст до указанной длины.

    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста

    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix


def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы Markdown V2.

    Args:
        text: Исходный текст

    Returns:
        Текст с экранированными символами
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for char in special_chars:
        text = text.replace(char, f'\\{char}')

    return text


def format_user_mention(user_id: int, name: str, username: Optional[str] = None) -> str:
    """
    Форматирует упоминание пользователя.

    Args:
        user_id: Telegram ID пользователя
        name: Имя пользователя
        username: Username (опционально)

    Returns:
        HTML-ссылка на пользователя
    """
    if username:
        return f'@{username}'
    return f'<a href="tg://user?id={user_id}">{name}</a>'