"""
Inline-клавиатуры бота.

Кнопки, прикреплённые к сообщениям.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Ad, AdStatus, AD_CATEGORIES, REPORT_REASONS_DISPLAY, ReportReason


def get_ad_actions_keyboard(ad_id: int, owner_id: int, viewer_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура действий с объявлением.

    Args:
        ad_id: ID объявления
        owner_id: ID владельца объявления
        viewer_id: ID просматривающего пользователя
    """
    builder = InlineKeyboardBuilder()

    if viewer_id == owner_id:
        # Кнопки для владельца
        builder.row(
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=f"ad:edit:{ad_id}"
            ),
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"ad:delete:{ad_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🔒 Сдано в аренду",
                callback_data=f"ad:rent:{ad_id}"
            ),
            InlineKeyboardButton(
                text="🚫 Закрыть",
                callback_data=f"ad:close:{ad_id}"
            )
        )
    else:
        # Кнопки для просматривающего
        builder.row(
            InlineKeyboardButton(
                text="📞 Связаться",
                callback_data=f"ad:contact:{ad_id}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="⚠️ Пожаловаться",
                callback_data=f"ad:report:{ad_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back:main"
        )
    )

    return builder.as_markup()


def get_my_ads_keyboard(ads: list[Ad]) -> InlineKeyboardMarkup:
    """
    Клавиатура списка объявлений пользователя.

    Args:
        ads: Список объявлений
    """
    builder = InlineKeyboardBuilder()

    status_emoji = {
        AdStatus.PENDING: "⏳",
        AdStatus.ACTIVE: "✅",
        AdStatus.REJECTED: "❌",
        AdStatus.RENTED: "🔒",
        AdStatus.CLOSED: "🚫"
    }

    for ad in ads[:10]:  # Максимум 10 объявлений
        emoji = status_emoji.get(ad.status, "📦")
        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} {ad.title[:30]}",
                callback_data=f"myad:view:{ad.id}"
            )
        )

    if not ads:
        builder.row(
            InlineKeyboardButton(
                text="📝 Создать объявление",
                callback_data="ad:create"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="back:main"
        )
    )

    return builder.as_markup()


def get_ad_edit_fields_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора поля для редактирования.

    Args:
        ad_id: ID объявления
    """
    builder = InlineKeyboardBuilder()

    fields = [
        ("📝 Название", "title"),
        ("📋 Описание", "description"),
        ("💰 Цена", "price"),
        ("📍 Местоположение", "location"),
        ("🏷 Категория", "category"),
        ("📞 Контакт", "contact"),
        ("📷 Фото", "photo")
    ]

    for label, field in fields:
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"edit:{field}:{ad_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="✅ Готово",
            callback_data=f"edit:done:{ad_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"edit:cancel:{ad_id}"
        )
    )

    return builder.as_markup()


def get_categories_inline_keyboard(prefix: str = "cat") -> InlineKeyboardMarkup:
    """
    Inline-клавиатура выбора категории.

    Args:
        prefix: Префикс для callback_data
    """
    builder = InlineKeyboardBuilder()

    for i in range(0, len(AD_CATEGORIES), 2):
        row = []
        for cat in AD_CATEGORIES[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=cat,
                    callback_data=f"{prefix}:{cat}"
                )
            )
        builder.row(*row)

    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"{prefix}:cancel"
        )
    )

    return builder.as_markup()


def get_pagination_keyboard(
        current_page: int,
        total_pages: int,
        prefix: str
) -> InlineKeyboardMarkup:
    """
    Клавиатура пагинации.

    Args:
        current_page: Текущая страница
        total_pages: Всего страниц
        prefix: Префикс для callback_data
    """
    builder = InlineKeyboardBuilder()

    buttons = []

    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"{prefix}:page:{current_page - 1}"
            )
        )

    buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop"
        )
    )

    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Вперёд ▶️",
                callback_data=f"{prefix}:page:{current_page + 1}"
            )
        )

    builder.row(*buttons)

    builder.row(
        InlineKeyboardButton(
            text="🏠 В меню",
            callback_data="back:main"
        )
    )

    return builder.as_markup()


def get_search_results_keyboard(ads: list[Ad], page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Клавиатура результатов поиска.

    Args:
        ads: Список найденных объявлений
        page: Текущая страница
        per_page: Объявлений на странице
    """
    builder = InlineKeyboardBuilder()

    start = (page - 1) * per_page
    end = start + per_page
    page_ads = ads[start:end]

    for ad in page_ads:
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {ad.title[:35]} — {ad.price_display}",
                callback_data=f"view:ad:{ad.id}"
            )
        )

    # Пагинация
    total_pages = (len(ads) + per_page - 1) // per_page
    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=f"search:page:{page - 1}")
        )

    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop")
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=f"search:page:{page + 1}")
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search:new"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="back:main")
    )

    return builder.as_markup()


def get_report_reasons_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора причины жалобы.

    Args:
        ad_id: ID объявления
    """
    builder = InlineKeyboardBuilder()

    for reason, label in REPORT_REASONS_DISPLAY.items():
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"report:{reason.value}:{ad_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="report:cancel"
        )
    )

    return builder.as_markup()


def get_moderation_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура модерации объявления.

    Args:
        ad_id: ID объявления
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=f"mod:approve:{ad_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"mod:reject:{ad_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⏭ Пропустить",
            callback_data=f"mod:skip:{ad_id}"
        )
    )

    return builder.as_markup()


def get_confirm_delete_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"confirm:delete:{ad_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"confirm:cancel:{ad_id}"
        )
    )

    return builder.as_markup()


def get_subscriptions_keyboard(subscriptions: list, user_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура управления подписками.

    Args:
        subscriptions: Список подписок пользователя
        user_id: ID пользователя
    """
    builder = InlineKeyboardBuilder()

    for sub in subscriptions[:5]:
        status = "✅" if sub.is_active else "⏸"
        criteria = sub.keywords or sub.category or sub.location or "Все"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {criteria[:25]}",
                callback_data=f"sub:toggle:{sub.id}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"sub:delete:{sub.id}"
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="➕ Новая подписка",
            callback_data="sub:create"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="back:main"
        )
    )

    return builder.as_markup()


def get_rating_inline_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """Inline-клавиатура выбора оценки."""
    builder = InlineKeyboardBuilder()

    builder.row(*[
        InlineKeyboardButton(
            text=f"{'⭐' * i}",
            callback_data=f"rate:{i}:{ad_id}"
        )
        for i in range(1, 6)
    ])

    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="rate:cancel"
        )
    )

    return builder.as_markup()