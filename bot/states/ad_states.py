"""
Состояния FSM для работы с объявлениями.

Конечный автомат для создания и редактирования объявлений.
"""

from aiogram.fsm.state import State, StatesGroup


class AdCreateStates(StatesGroup):
    """Состояния создания объявления."""

    waiting_for_title = State()  # Ожидание названия
    waiting_for_description = State()  # Ожидание описания
    waiting_for_price = State()  # Ожидание цены
    waiting_for_location = State()  # Ожидание местоположения
    waiting_for_category = State()  # Ожидание выбора категории
    waiting_for_contact = State()  # Ожидание контактной информации
    waiting_for_photo = State()  # Ожидание фото (опционально)
    confirm = State()  # Подтверждение


class AdEditStates(StatesGroup):
    """Состояния редактирования объявления."""

    select_ad = State()  # Выбор объявления
    select_field = State()  # Выбор поля для редактирования
    waiting_for_title = State()  # Новое название
    waiting_for_description = State()  # Новое описание
    waiting_for_price = State()  # Новая цена
    waiting_for_location = State()  # Новое местоположение
    waiting_for_category = State()  # Новая категория
    waiting_for_contact = State()  # Новый контакт
    waiting_for_photo = State()  # Новое фото
    confirm = State()  # Подтверждение изменений


class AdDeleteStates(StatesGroup):
    """Состояния удаления объявления."""

    select_ad = State()  # Выбор объявления
    confirm = State()  # Подтверждение удаления