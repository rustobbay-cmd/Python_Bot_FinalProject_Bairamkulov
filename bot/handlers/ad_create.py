"""
Обработчики создания объявлений.

Полный цикл создания нового объявления с валидацией.
"""

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import AdCreateStates
from bot.keyboards import (
    get_cancel_keyboard,
    get_categories_keyboard,
    get_contact_keyboard,
    get_photo_keyboard,
    get_confirm_keyboard,
    get_main_menu
)
from database.models import User, AD_CATEGORIES
from services import AdService, UserService
from services.notification_service import NotificationService
from utils.validators import (
    validate_title,
    validate_description,
    validate_price,
    validate_location,
    validate_phone
)

router = Router(name="ad_create")


@router.message(Command("new_ad"))
@router.message(F.text == "📝 Разместить объявление")
async def start_ad_creation(message: Message, state: FSMContext):
    """Начало создания объявления."""
    await state.clear()
    await state.set_state(AdCreateStates.waiting_for_title)

    await message.answer(
        "📝 <b>Создание объявления</b>\n\n"
        "Шаг 1/6: Введите <b>название товара</b>\n\n"
        "Например: <i>Перфоратор Bosch</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdCreateStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Обработка названия товара."""
    title = validate_title(message.text)

    if not title:
        await message.answer(
            "❌ Некорректное название.\n\n"
            "Название должно быть от 3 до 200 символов.\n"
            "Попробуйте ещё раз:"
        )
        return

    await state.update_data(title=title)
    await state.set_state(AdCreateStates.waiting_for_description)

    await message.answer(
        "✅ Название сохранено!\n\n"
        "Шаг 2/6: Введите <b>описание товара</b>\n\n"
        "Опишите состояние, особенности, что входит в комплект.",
        parse_mode="HTML"
    )


@router.message(AdCreateStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания товара."""
    description = validate_description(message.text)

    if not description:
        await message.answer(
            "❌ Некорректное описание.\n\n"
            "Описание должно быть от 10 до 2000 символов.\n"
            "Попробуйте ещё раз:"
        )
        return

    await state.update_data(description=description)
    await state.set_state(AdCreateStates.waiting_for_price)

    await message.answer(
        "✅ Описание сохранено!\n\n"
        "Шаг 3/6: Введите <b>стоимость аренды за день</b> (в рублях)\n\n"
        "Например: <i>500</i> или <i>1500</i>",
        parse_mode="HTML"
    )


@router.message(AdCreateStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    """Обработка цены."""
    price = validate_price(message.text)

    if not price:
        await message.answer(
            "❌ Некорректная цена.\n\n"
            "Введите число от 1 до 10 000 000 рублей.\n"
            "Например: 500"
        )
        return

    await state.update_data(price=str(price))
    await state.set_state(AdCreateStates.waiting_for_location)

    await message.answer(
        "✅ Цена сохранена!\n\n"
        "Шаг 4/6: Введите <b>местоположение</b> товара\n\n"
        "Например: <i>Москва, м. Арбатская</i>",
        parse_mode="HTML"
    )


@router.message(AdCreateStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext):
    """Обработка местоположения."""
    location = validate_location(message.text)

    if not location:
        await message.answer(
            "❌ Некорректное местоположение.\n\n"
            "Укажите город и район/станцию метро.\n"
            "Попробуйте ещё раз:"
        )
        return

    await state.update_data(location=location)
    await state.set_state(AdCreateStates.waiting_for_category)

    await message.answer(
        "✅ Местоположение сохранено!\n\n"
        "Шаг 5/6: Выберите <b>категорию</b> товара:",
        reply_markup=get_categories_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdCreateStates.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    """Обработка выбора категории."""
    if message.text not in AD_CATEGORIES:
        await message.answer(
            "❌ Выберите категорию из предложенных кнопок:",
            reply_markup=get_categories_keyboard()
        )
        return

    await state.update_data(category=message.text)
    await state.set_state(AdCreateStates.waiting_for_contact)

    await message.answer(
        "✅ Категория выбрана!\n\n"
        "Шаг 6/6: Укажите <b>контактную информацию</b>\n\n"
        "Вы можете отправить номер телефона или ввести вручную.",
        reply_markup=get_contact_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdCreateStates.waiting_for_contact, F.contact)
async def process_contact_shared(message: Message, state: FSMContext):
    """Обработка отправленного контакта."""
    phone = message.contact.phone_number
    formatted_phone = validate_phone(phone)

    if formatted_phone:
        await state.update_data(contact=formatted_phone)
    else:
        await state.update_data(contact=phone)

    await ask_for_photo(message, state)


@router.message(AdCreateStates.waiting_for_contact, F.text == "✍️ Ввести вручную")
async def process_contact_manual_start(message: Message, state: FSMContext):
    """Переход к ручному вводу контакта."""
    await message.answer(
        "Введите номер телефона или Telegram username:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AdCreateStates.waiting_for_contact)
async def process_contact_text(message: Message, state: FSMContext):
    """Обработка текстового контакта."""
    contact = message.text.strip()

    # Пробуем как телефон
    formatted_phone = validate_phone(contact)
    if formatted_phone:
        contact = formatted_phone

    # Проверяем минимальную длину
    if len(contact) < 5:
        await message.answer(
            "❌ Некорректный контакт.\n\n"
            "Введите номер телефона или Telegram username."
        )
        return

    await state.update_data(contact=contact)
    await ask_for_photo(message, state)


async def ask_for_photo(message: Message, state: FSMContext):
    """Запрос фотографии товара."""
    await state.set_state(AdCreateStates.waiting_for_photo)

    await message.answer(
        "✅ Контакт сохранён!\n\n"
        "📷 <b>Добавьте фото товара</b> (необязательно)\n\n"
        "Отправьте фото или нажмите «Без фото».",
        reply_markup=get_photo_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdCreateStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обработка фотографии."""
    # Берём фото лучшего качества
    photo = message.photo[-1]
    await state.update_data(photo_id=photo.file_id)

    await show_confirmation(message, state)


@router.message(AdCreateStates.waiting_for_photo, F.text == "⏭ Без фото")
async def skip_photo(message: Message, state: FSMContext):
    """Пропуск фотографии."""
    await state.update_data(photo_id=None)
    await show_confirmation(message, state)


async def show_confirmation(message: Message, state: FSMContext):
    """Показ превью объявления для подтверждения."""
    data = await state.get_data()
    await state.set_state(AdCreateStates.confirm)

    preview = (
        "📋 <b>Проверьте объявление:</b>\n\n"
        f"📦 <b>Название:</b> {data['title']}\n\n"
        f"📝 <b>Описание:</b>\n{data['description']}\n\n"
        f"💰 <b>Цена:</b> {data['price']} ₽/день\n"
        f"📍 <b>Место:</b> {data['location']}\n"
        f"🏷 <b>Категория:</b> {data['category']}\n"
        f"📞 <b>Контакт:</b> {data['contact']}\n"
        f"📷 <b>Фото:</b> {'Да' if data.get('photo_id') else 'Нет'}\n\n"
        "Всё верно?"
    )

    if data.get('photo_id'):
        await message.answer_photo(
            photo=data['photo_id'],
            caption=preview,
            reply_markup=get_confirm_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            preview,
            reply_markup=get_confirm_keyboard(),
            parse_mode="HTML"
        )


@router.message(AdCreateStates.confirm, F.text == "✅ Подтвердить")
async def confirm_ad_creation(
        message: Message,
        state: FSMContext,
        db_user: User,
        ad_service: AdService,
        bot: Bot
):
    """Подтверждение и создание объявления."""
    data = await state.get_data()

    from decimal import Decimal

    # Создаём объявление
    ad = await ad_service.create(
        owner_id=db_user.id,
        title=data['title'],
        description=data['description'],
        price_per_day=Decimal(data['price']),
        location=data['location'],
        category=data['category'],
        contact_info=data['contact'],
        photo_id=data.get('photo_id')
    )

    await state.clear()

    # Уведомляем админов
    from database import db
    async with db.session_factory() as session:
        notification_service = NotificationService(session, bot)
        await notification_service.notify_new_ad_for_moderation(ad)

    await message.answer(
        f"✅ <b>Объявление #{ad.id} создано!</b>\n\n"
        "Оно отправлено на модерацию.\n"
        "Вы получите уведомление после проверки.\n\n"
        "Обычно модерация занимает до 24 часов.",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )