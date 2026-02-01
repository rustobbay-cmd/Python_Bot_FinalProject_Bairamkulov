"""
Состояния FSM для поиска объявлений.

Конечный автомат для расширенного поиска с фильтрами.
"""

from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    """Состояния поиска объявлений."""

    select_type = State()  # Выбор типа поиска
    waiting_for_keywords = State()  # Ввод ключевых слов
    waiting_for_location = State()  # Ввод местоположения
    waiting_for_category = State()  # Выбор категории
    waiting_for_min_price = State()  # Минимальная цена
    waiting_for_max_price = State()  # Максимальная цена
    show_results = State()  # Показ результатов


class SubscriptionStates(StatesGroup):
    """Состояния создания подписки на уведомления."""

    select_type = State()  # Выбор типа критерия
    waiting_for_keywords = State()  # Ввод ключевых слов
    waiting_for_category = State()  # Выбор категории
    waiting_for_location = State()  # Ввод местоположения
    waiting_for_max_price = State()  # Максимальная цена
    confirm = State()  # Подтверждение