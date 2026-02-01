"""
Обработчики обратной связи.

Отзывы о товарах, жалобы на объявления.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import FeedbackStates, ReportStates
from bot.keyboards import (
    get_feedback_type_keyboard,
    get_rating_keyboard,
    get_cancel_keyboard,
    get_report_reasons_keyboard,
    get_main_menu
)
from database.models import User, FeedbackType, Feedback, ReportReason
from services import AdService, ModerationService
from sqlalchemy.ext.asyncio import AsyncSession

router = Router(name="feedback")


@router.message(Command("feedback"))
@router.message(F.text == "💬 Обратная связь")
async def start_feedback(message: Message, state: FSMContext):
    """Начало создания отзыва."""
    await state.clear()
    await state.set_state(FeedbackStates.select_type)

    await message.answer(
        "💬 <b>Обратная связь</b>\n\n"
        "Выберите тип отзыва:",
        reply_markup=get_feedback_type_keyboard(),
        parse_mode="HTML"
    )


@router.message(FeedbackStates.select_type, F.text == "🤖 О боте")
async def feedback_about_bot(message: Message, state: FSMContext):
    """Отзыв о работе бота."""
    await state.update_data(feedback_type=FeedbackType.BOT, ad_id=None)
    await state.set_state(FeedbackStates.waiting_for_rating)

    await message.answer(
        "⭐ Оцените работу бота от 1 до 5:",
        reply_markup=get_rating_keyboard()
    )


@router.message(FeedbackStates.select_type, F.text == "📦 О товаре")
async def feedback_about_ad(message: Message, state: FSMContext, ad_service: AdService, db_user: User):
    """Отзыв о товаре."""
    # Получаем активные объявления, которые пользователь мог арендовать
    # Для простоты - любое активное объявление не своё
    await state.update_data(feedback_type=FeedbackType.AD)
    await state.set_state(FeedbackStates.waiting_for_rating)

    await message.answer(
        "Введите ID объявления (можно найти в описании объявления)\n"
        "или отправьте /skip чтобы оставить общий отзыв:",
        reply_markup=get_cancel_keyboard()
    )


@router.message(FeedbackStates.waiting_for_rating)
async def process_rating(message: Message, state: FSMContext):
    """Обработка оценки."""
    rating_map = {
        "1 ⭐": 1, "2 ⭐": 2, "3 ⭐": 3, "4 ⭐": 4, "5 ⭐": 5
    }

    rating = rating_map.get(message.text)

    if not rating:
        try:
            rating = int(message.text)
            if not 1 <= rating <= 5:
                raise ValueError
        except ValueError:
            await message.answer("❌ Выберите оценку от 1 до 5")
            return

    await state.update_data(rating=rating)
    await state.set_state(FeedbackStates.waiting_for_text)

    await message.answer(
        "📝 Напишите ваш отзыв (или /skip чтобы пропустить):",
        reply_markup=get_cancel_keyboard()
    )


@router.message(FeedbackStates.waiting_for_text)
async def process_feedback_text(
        message: Message,
        state: FSMContext,
        session: AsyncSession,
        db_user: User
):
    """Обработка текста отзыва и сохранение."""
    text = None if message.text == "/skip" else message.text

    data = await state.get_data()

    feedback = Feedback(
        user_id=db_user.id,
        feedback_type=data['feedback_type'],
        rating=data['rating'],
        text=text,
        ad_id=data.get('ad_id')
    )

    session.add(feedback)
    await session.commit()

    await state.clear()

    await message.answer(
        f"✅ <b>Спасибо за отзыв!</b>\n\n"
        f"Ваша оценка: {'⭐' * data['rating']}\n"
        f"{'📝 ' + text[:100] + '...' if text and len(text) > 100 else '📝 ' + text if text else ''}",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


# === Жалобы ===

@router.callback_query(F.data.startswith("ad:report:"))
async def start_report(callback: CallbackQuery, state: FSMContext):
    """Начало создания жалобы."""
    ad_id = int(callback.data.split(":")[2])

    await state.set_state(ReportStates.select_reason)
    await state.update_data(report_ad_id=ad_id)

    await callback.message.answer(
        "⚠️ <b>Жалоба на объявление</b>\n\n"
        "Выберите причину:",
        reply_markup=get_report_reasons_keyboard(ad_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("report:"), ReportStates.select_reason)
async def select_report_reason(callback: CallbackQuery, state: FSMContext):
    """Выбор причины жалобы."""
    parts = callback.data.split(":")
    reason_str = parts[1]

    if reason_str == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Жалоба отменена")
        await callback.answer()
        return

    try:
        reason = ReportReason(reason_str)
    except ValueError:
        await callback.answer("Неизвестная причина")
        return

    await state.update_data(report_reason=reason)
    await state.set_state(ReportStates.waiting_for_description)

    await callback.message.answer(
        "📝 Опишите нарушение подробнее (или /skip):",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(ReportStates.waiting_for_description)
async def process_report_description(
        message: Message,
        state: FSMContext,
        moderation_service: ModerationService,
        db_user: User
):
    """Обработка описания и создание жалобы."""
    description = None if message.text == "/skip" else message.text

    data = await state.get_data()

    report = await moderation_service.create_report(
        ad_id=data['report_ad_id'],
        reporter_id=db_user.id,
        reason=data['report_reason'],
        description=description
    )

    await state.clear()

    await message.answer(
        f"✅ <b>Жалоба #{report.id} отправлена</b>\n\n"
        "Модераторы рассмотрят её в ближайшее время.\n"
        "Спасибо за помощь в поддержании качества!",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


# === Обработка жалоб для админов ===

@router.message(F.text == "🚨 Жалобы")
async def show_reports(
        message: Message,
        moderation_service: ModerationService
):
    """Показать жалобы (для админов)."""
    from bot.filters import IsAdminFilter
    # Проверка админа через фильтр роутера moderation

    reports = await moderation_service.get_pending_reports()

    if not reports:
        await message.answer(
            "✅ <b>Нет жалоб на рассмотрении</b>",
            parse_mode="HTML"
        )
        return

    text = f"🚨 <b>Жалобы ({len(reports)})</b>\n\n"

    for report in reports[:10]:
        text += (
            f"#{report.id} — {report.reason_display}\n"
            f"📦 Объявление: {report.ad.title[:30] if report.ad else 'Удалено'}\n"
            f"👤 От: {report.reporter.full_name}\n\n"
        )

    await message.answer(text, parse_mode="HTML")