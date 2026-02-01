"""Клавиатуры бота."""

from .reply import (
    get_main_menu,
    get_cancel_keyboard,
    get_skip_keyboard,
    get_confirm_keyboard,
    get_categories_keyboard,
    get_contact_keyboard,
    get_photo_keyboard,
    get_rating_keyboard,
    get_feedback_type_keyboard,
    get_search_type_keyboard,
    get_admin_menu,
    remove_keyboard
)
from .inline import (
    get_ad_actions_keyboard,
    get_my_ads_keyboard,
    get_ad_edit_fields_keyboard,
    get_categories_inline_keyboard,
    get_pagination_keyboard,
    get_search_results_keyboard,
    get_report_reasons_keyboard,
    get_moderation_keyboard,
    get_confirm_delete_keyboard,
    get_subscriptions_keyboard,
    get_rating_inline_keyboard
)

__all__ = [
    # Reply keyboards
    "get_main_menu",
    "get_cancel_keyboard",
    "get_skip_keyboard",
    "get_confirm_keyboard",
    "get_categories_keyboard",
    "get_contact_keyboard",
    "get_photo_keyboard",
    "get_rating_keyboard",
    "get_feedback_type_keyboard",
    "get_search_type_keyboard",
    "get_admin_menu",
    "remove_keyboard",
    # Inline keyboards
    "get_ad_actions_keyboard",
    "get_my_ads_keyboard",
    "get_ad_edit_fields_keyboard",
    "get_categories_inline_keyboard",
    "get_pagination_keyboard",
    "get_search_results_keyboard",
    "get_report_reasons_keyboard",
    "get_moderation_keyboard",
    "get_confirm_delete_keyboard",
    "get_subscriptions_keyboard",
    "get_rating_inline_keyboard",
]