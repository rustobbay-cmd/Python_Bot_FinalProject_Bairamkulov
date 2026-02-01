"""
Состояния FSM для отзывов и жалоб.

Конечный автомат для обратной связи и модерации.
"""

from aiogram.fsm.state import State, StatesGroup


class FeedbackStates(StatesGroup):
    """Состояния отправки отзыва."""

    select_type = State()  # Выбор типа отзыва
    select_ad = State()  # Выбор объявления (для отзыва о товаре)
    waiting_for_rating = State()  # Ожидание оценки
    waiting_for_text = State()  # Ожидание текста
    confirm = State()  # Подтверждение


class ReportStates(StatesGroup):
    """Состояния отправки жалобы."""

    select_reason = State()  # Выбор причины
    waiting_for_description = State()  # Описание нарушения
    confirm = State()  # Подтверждение


class ModerationStates(StatesGroup):
    """Состояния модерации (для администраторов)."""

    view_ad = State()  # Просмотр объявления
    waiting_for_reason = State()  # Ввод причины отклонения
    view_report = State()  # Просмотр жалобы
    waiting_for_comment = State()  # Комментарий к решению