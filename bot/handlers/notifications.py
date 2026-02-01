"""
Обработчики подписок на уведомления.

Создание, управление и удаление подписок.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import SubscriptionStates
from bot.keyboards import (
    get_subscriptions_keyboard,
    get_cancel_keyboard,
    get_categories_keyboard,
    get_main_menu
)
from database.models import User
from services.notification_service import SubscriptionService

router = Router(name="notifications")


@router.message(Command("subscriptions"))
@router.message(F.text == "🔔 Подписки")
async def show_subscriptions(
        message: Message,
        state: FSMContext,
        subscription_service: SubscriptionService,
        db_user: User
):
    """Показать подписки пользователя."""
    await state.clear()

    subscriptions = await subscription_service.get_user_subscriptions(db_user.id)

    if not subscriptions:
        await message.answer(
            "🔔 <b>У вас нет активных подписок</b>\n\n"
            "Подписка позволяет получать уведомления о новых объявлениях "
            "по заданным критериям (ключевые слова, категория, город, цена).\n\n"
            "Хотите создать подписку?",
            reply_markup=get_subscriptions_keyboard([], db_user.id),
            parse_mode="HTML"
        )
        return

    text = "🔔 <b>Ваши подписки</b>\n\n"

    for sub in subscriptions:
        text += sub.format_display() + "\n\n"

    await message.answer(
        text,
        reply_markup=get_subscriptions_keyboard(subscriptions, db_user.id),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "sub:create")
async def start_create_subscription(callback: CallbackQuery, state: FSMContext):
    """Начало создания подписки."""
    await state.set_state(SubscriptionStates.select_type)
    await state.update_data(
        sub_keywords=None,
        sub_category=None,
        sub_location=None,
        sub_max_price=None
    )

    await callback.message.answer(
        "🔔 <b>Создание подписки</b>\n\n"
        "Введите <b>ключевые слова</b> для поиска\n"
        "(или /skip чтобы пропустить):\n\n"
        "Например: <i>велосипед</i>, <i>дрель</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(SubscriptionStates.select_type)
async def process_subscription_keywords(message: Message, state: FSMContext):
    """Обработка ключевых слов подписки."""
    if message.text != "/skip":
        await state.update_data(sub_keywords=message.text.strip())

    await state.set_state(SubscriptionStates.waiting_for_category)

    await message.answer(
        "🏷 Выберите <b>категорию</b> (или /skip):",
        reply_markup=get_categories_keyboard(),
        parse_mode="HTML"
    )


@router.message(SubscriptionStates.waiting_for_category)
async def process_subscription_category(message: Message, state: FSMContext):
    """Обработка категории подписки."""
    from database.models import AD_CATEGORIES

    if message.text != "/skip":
        if message.text in AD_CATEGORIES:
            await state.update_data(sub_category=message.text)
        else:
            await message.answer("❌ Выберите категорию из списка или /skip")
            return

    await state.set_state(SubscriptionStates.waiting_for_location)

    await message.answer(
        "📍 Введите <b>город/район</b> (или /skip):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(SubscriptionStates.waiting_for_location)
async def process_subscription_location(message: Message, state: FSMContext):
    """Обработка местоположения подписки."""
    if message.text != "/skip":
        await state.update_data(sub_location=message.text.strip())

    await state.set_state(SubscriptionStates.waiting_for_max_price)

    await message.answer(
        "💰 Введите <b>максимальную цену</b> за день (или /skip):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(SubscriptionStates.waiting_for_max_price)
async def process_subscription_max_price(
        message: Message,
        state: FSMContext,
        subscription_service: SubscriptionService,
        db_user: User
):
    """Обработка максимальной цены и создание подписки."""
    max_price = None

    if message.text != "/skip":
        from utils.validators import validate_price
        max_price = validate_price(message.text)

        if max_price is None:
            await message.answer("❌ Введите корректную цену или /skip")
            return

        max_price = float(max_price)

    data = await state.get_data()

    # Проверяем, что хотя бы один критерий задан
    if not any([
        data.get('sub_keywords'),
        data.get('sub_category'),
        data.get('sub_location'),
        max_price
    ]):
        await message.answer(
            "❌ Укажите хотя бы один критерий для подписки.\n"
            "Начните заново с /subscriptions"
        )
        await state.clear()
        return

    # Создаём подписку
    subscription = await subscription_service.create(
        user_id=db_user.id,
        keywords=data.get('sub_keywords'),
        category=data.get('sub_category'),
        location=data.get('sub_location'),
        max_price=max_price
    )

    await state.clear()

    await message.answer(
        f"✅ <b>Подписка создана!</b>\n\n"
        f"{subscription.format_display()}\n\n"
        "Вы будете получать уведомления о новых объявлениях, "
        "соответствующих этим критериям.",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sub:toggle:"))
async def toggle_subscription(
        callback: CallbackQuery,
        subscription_service: SubscriptionService,
        db_user: User
):
    """Переключить активность подписки."""
    sub_id = int(callback.data.split(":")[2])

    success = await subscription_service.toggle_subscription(sub_id, db_user.id)

    if success:
        await callback.answer("✅ Статус изменён")
        # Обновляем список
        subscriptions = await subscription_service.get_user_subscriptions(db_user.id)

        text = "🔔 <b>Ваши подписки</b>\n\n"
        for sub in subscriptions:
            text += sub.format_display() + "\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_subscriptions_keyboard(subscriptions, db_user.id),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Не удалось изменить", show_alert=True)


@router.callback_query(F.data.startswith("sub:delete:"))
async def delete_subscription(
        callback: CallbackQuery,
        subscription_service: SubscriptionService,
        db_user: User
):
    """Удалить подписку."""
    sub_id = int(callback.data.split(":")[2])

    success = await subscription_service.delete_subscription(sub_id, db_user.id)

    if success:
        await callback.answer("🗑 Подписка удалена")
        # Обновляем список
        subscriptions = await subscription_service.get_user_subscriptions(db_user.id)

        if subscriptions:
            text = "🔔 <b>Ваши подписки</b>\n\n"
            for sub in subscriptions:
                text += sub.format_display() + "\n\n"
        else:
            text = "🔔 <b>У вас нет активных подписок</b>"

        await callback.message.edit_text(
            text,
            reply_markup=get_subscriptions_keyboard(subscriptions, db_user.id),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Не удалось удалить", show_alert=True)