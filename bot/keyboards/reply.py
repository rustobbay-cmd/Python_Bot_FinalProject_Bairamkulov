"""
Reply-клавиатуры бота.

Кнопки, отображающиеся под полем ввода.
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database.models import AD_CATEGORIES


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота."""
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="📝 Разместить объявление"),
        KeyboardButton(text="🔍 Поиск")
    )
    builder.row(
        KeyboardButton(text="📋 Мои объявления"),
        KeyboardButton(text="🔔 Подписки")
    )
    builder.row(
        KeyboardButton(text="💬 Обратная связь"),
        KeyboardButton(text="ℹ️ Помощь")
    )

    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками Пропустить и Отмена."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭ Пропустить"),
        KeyboardButton(text="❌ Отмена")
    )
    return builder.as_markup(resize_keyboard=True)


def get_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="✅ Подтвердить"),
        KeyboardButton(text="❌ Отмена")
    )
    return builder.as_markup(resize_keyboard=True)


def get_categories_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора категории."""
    builder = ReplyKeyboardBuilder()

    # Добавляем категории по 2 в ряд
    for i in range(0, len(AD_CATEGORIES), 2):
        row_buttons = [KeyboardButton(text=cat) for cat in AD_CATEGORIES[i:i + 2]]
        builder.row(*row_buttons)

    builder.row(KeyboardButton(text="❌ Отмена"))

    return builder.as_markup(resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с запросом контакта."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)
    )
    builder.row(
        KeyboardButton(text="✍️ Ввести вручную"),
        KeyboardButton(text="❌ Отмена")
    )
    return builder.as_markup(resize_keyboard=True)


def get_photo_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для добавления фото."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="⏭ Без фото"),
        KeyboardButton(text="❌ Отмена")
    )
    return builder.as_markup(resize_keyboard=True)


def get_rating_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора оценки."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="1 ⭐"),
        KeyboardButton(text="2 ⭐"),
        KeyboardButton(text="3 ⭐"),
        KeyboardButton(text="4 ⭐"),
        KeyboardButton(text="5 ⭐")
    )
    builder.row(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def get_feedback_type_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа отзыва."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📦 О товаре"),
        KeyboardButton(text="🤖 О боте")
    )
    builder.row(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def get_search_type_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа поиска."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🔤 По ключевым словам"),
        KeyboardButton(text="📍 По городу")
    )
    builder.row(
        KeyboardButton(text="🏷 По категории"),
        KeyboardButton(text="💰 По цене")
    )
    builder.row(
        KeyboardButton(text="🔎 Расширенный поиск"),
        KeyboardButton(text="❌ Отмена")
    )
    return builder.as_markup(resize_keyboard=True)


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Админ-меню."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📬 Модерация"),
        KeyboardButton(text="🚨 Жалобы")
    )
    builder.row(
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="👥 Пользователи")
    )
    builder.row(KeyboardButton(text="🏠 Главное меню"))
    return builder.as_markup(resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    """Удаляет клавиатуру."""
    return ReplyKeyboardRemove()