"""
Обработчики модерации.

Функционал для администраторов: одобрение/отклонение объявлений.
"""

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import ModerationStates
from bot.filters import IsAdminFilter
from bot.keyboards import (
    get_moderation_keyboard,
    get_cancel_keyboard,
    get_admin_menu
)
from database.models import User, Ad
from services import ModerationService, AdService
from services.notification_service import NotificationService

router = Router(name="moderation")
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


@router.message(Command("moderate"))
@router.message(F.text == "📬 Модерация")
async def show_moderation_queue(
        message: Message,
        state: FSMContext,
        moderation_service: ModerationService
):
    """Показать очередь модерации."""
    await state.clear()

    pending = await moderation_service.get_pending_ads()

    if not pending:
        await message.answer(
            "✅ <b>Очередь модерации пуста</b>\n\n"
            "Новых объявлений на проверку нет.",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
        return

    await state.update_data(moderation_queue=[ad.id for ad in pending], current_index=0)
    await show_ad_for_moderation(message, pending[0])


async def show_ad_for_moderation(message: Message, ad: Ad):
    """Показать объявление для модерации."""
    text = (
        f"📬 <b>Модерация #{ad.id}</b>\n\n"
        f"{ad.format_full()}\n\n"
        f"👤 <b>Автор:</b> {ad.owner.full_name}\n"
        f"📅 <b>Создано:</b> {ad.created_at.strftime('%d.%m.%Y %H:%M')}"
    )

    if ad.photo_id:
        await message.answer_photo(
            photo=ad.photo_id,
            caption=text,
            reply_markup=get_moderation_keyboard(ad.id),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=get_moderation_keyboard(ad.id),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("mod:approve:"))
async def approve_ad(
        callback: CallbackQuery,
        state: FSMContext,
        moderation_service: ModerationService,
        db_user: User,
        bot: Bot
):
    """Одобрить объявление."""
    ad_id = int(callback.data.split(":")[2])

    ad = await moderation_service.approve_ad(ad_id, db_user.id)

    if not ad:
        await callback.answer("❌ Объявление не найдено", show_alert=True)
        return

    # Уведомляем владельца
    from database import db
    async with db.session_factory() as session:
        notification_service = NotificationService(session, bot)
        await notification_service.notify_ad_approved(ad)
        # Уведомляем подписчиков
        await notification_service.notify_new_ad(ad)

    await callback.message.edit_caption(
        caption=f"✅ <b>Объявление #{ad_id} одобрено</b>",
        parse_mode="HTML"
    ) if callback.message.photo else await callback.message.edit_text(
        f"✅ <b>Объявление #{ad_id} одобрено</b>",
        parse_mode="HTML"
    )

    await show_next_in_queue(callback, state, moderation_service)
    await callback.answer("✅ Одобрено")


@router.callback_query(F.data.startswith("mod:reject:"))
async def start_reject_ad(callback: CallbackQuery, state: FSMContext):
    """Начать отклонение объявления."""
    ad_id = int(callback.data.split(":")[2])

    await state.set_state(ModerationStates.waiting_for_reason)
    await state.update_data(rejecting_ad_id=ad_id)

    await callback.message.answer(
        "❌ <b>Отклонение объявления</b>\n\n"
        "Укажите причину отклонения:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(ModerationStates.waiting_for_reason)
async def process_rejection_reason(
        message: Message,
        state: FSMContext,
        moderation_service: ModerationService,
        db_user: User,
        bot: Bot
):
    """Обработка причины отклонения."""
    reason = message.text.strip()

    if len(reason) < 5:
        await message.answer("❌ Причина слишком короткая")
        return

    data = await state.get_data()
    ad_id = data.get("rejecting_ad_id")

    ad = await moderation_service.reject_ad(ad_id, db_user.id, reason)

    if not ad:
        await message.answer("❌ Объявление не найдено")
        await state.clear()
        return

    # Уведомляем владельца
    from database import db
    async with db.session_factory() as session:
        notification_service = NotificationService(session, bot)
        await notification_service.notify_ad_rejected(ad)

    await message.answer(
        f"❌ <b>Объявление #{ad_id} отклонено</b>\n\n"
        f"Причина: {reason}",
        parse_mode="HTML"
    )

    # Показываем следующее
    pending = await moderation_service.get_pending_ads()

    if pending:
        await state.update_data(
            moderation_queue=[a.id for a in pending],
            current_index=0
        )
        await state.set_state(None)
        await show_ad_for_moderation(message, pending[0])
    else:
        await state.clear()
        await message.answer(
            "✅ Очередь модерации пуста",
            reply_markup=get_admin_menu()
        )


@router.callback_query(F.data.startswith("mod:skip:"))
async def skip_moderation(
        callback: CallbackQuery,
        state: FSMContext,
        moderation_service: ModerationService
):
    """Пропустить объявление."""
    await show_next_in_queue(callback, state, moderation_service)
    await callback.answer("⏭ Пропущено")


async def show_next_in_queue(
        callback: CallbackQuery,
        state: FSMContext,
        moderation_service: ModerationService
):
    """Показать следующее объявление в очереди."""
    pending = await moderation_service.get_pending_ads()

    if not pending:
        await state.clear()
        await callback.message.answer(
            "✅ <b>Очередь модерации пуста</b>",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
        return

    await state.update_data(
        moderation_queue=[a.id for a in pending],
        current_index=0
    )

    await show_ad_for_moderation(callback.message, pending[0])


@router.message(F.text == "📊 Статистика")
async def show_stats(
        message: Message,
        moderation_service: ModerationService,
        ad_service: AdService
):
    """Показать статистику."""
    from services import AdService, UserService
    from database import db

    mod_stats = await moderation_service.get_moderation_stats()
    ad_stats = await ad_service.get_stats()

    async with db.session_factory() as session:
        user_service = UserService(session)
        users_count = await user_service.get_users_count()

    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 <b>Пользователей:</b> {users_count}\n\n"
        f"📦 <b>Объявления:</b>\n"
        f"  • Всего: {ad_stats['total']}\n"
        f"  • Активных: {ad_stats['active']}\n"
        f"  • На модерации: {ad_stats['pending']}\n\n"
        f"📬 <b>Модерация:</b>\n"
        f"  • В очереди: {mod_stats['pending_ads']}\n"
        f"  • Одобрено сегодня: {mod_stats['approved_today']}\n"
        f"  • Жалоб на рассмотрении: {mod_stats['pending_reports']}"
    )

    await message.answer(text, parse_mode="HTML")