"""
Валидаторы данных.

Проверка корректности вводимых пользователем данных.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException


def validate_phone(phone: str, region: str = "RU") -> Optional[str]:
    """Валидирует и форматирует номер телефона."""
    try:
        cleaned = re.sub(r'[^\d+]', '', phone)
        if cleaned.startswith('8') and len(cleaned) == 11:
            cleaned = '+7' + cleaned[1:]
        elif not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        parsed = phonenumbers.parse(cleaned, region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        return None
    except NumberParseException:
        return None


def validate_price(price_str: str) -> Optional[Decimal]:
    """Валидирует и конвертирует строку цены в Decimal."""
    try:
        cleaned = price_str.strip().replace(',', '.').replace(' ', '')
        cleaned = cleaned.replace('₽', '').replace('р', '').replace('руб', '').strip()
        price = Decimal(cleaned)
        if price <= 0 or price > Decimal('10000000'):
            return None
        return price.quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return None


def validate_title(title: str) -> Optional[str]:
    """Валидирует заголовок объявления."""
    if not title:
        return None
    cleaned = ' '.join(title.split())
    if len(cleaned) < 3 or len(cleaned) > 200:
        return None
    spam_patterns = [r'(.)\1{5,}', r'https?://', r't\.me/']
    for pattern in spam_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return None
    return cleaned


def validate_description(description: str) -> Optional[str]:
    """Валидирует описание объявления."""
    if not description:
        return None
    cleaned = '\n'.join(' '.join(line.split()) for line in description.split('\n'))
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    if len(cleaned) < 10 or len(cleaned) > 2000:
        return None
    return cleaned


def validate_location(location: str) -> Optional[str]:
    """Валидирует местоположение."""
    if not location:
        return None
    cleaned = ' '.join(location.split())
    if len(cleaned) < 2 or len(cleaned) > 200:
        return None
    return cleaned


def validate_rating(rating: str) -> Optional[int]:
    """Валидирует оценку (1-5)."""
    try:
        value = int(rating)
        if 1 <= value <= 5:
            return value
        return None
    except (ValueError, TypeError):
        return None


def sanitize_html(text: str) -> str:
    """Очищает текст от HTML-тегов."""
    cleaned = re.sub(r'<[^>]+>', '', text)
    cleaned = cleaned.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return cleaned


def is_valid_telegram_username(username: str) -> bool:
    """Проверяет валидность Telegram username."""
    if username.startswith('@'):
        username = username[1:]
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$'
    return bool(re.match(pattern, username))