"""
Обработчики административной панели.

Управление пользователями, расширенная статистика.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.filters import IsAdminFilter
from bot.keyboards import get_admin_menu
from services import UserService, AdService, ModerationService
from database.models import User

router = Router(name="admin")
router.message.filter(IsAdminFilter())


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    """Открыть админ-панель."""
    await state.clear()

    await message.answer(
        "🔧 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "👥 Пользователи")
async def show_users_stats(
        message: Message,
        user_service: UserService
):
    """Статистика по пользователям."""
    total = await user_service.get_users_count()
    admins = await user_service.get_all_admins()

    text = (
        "👥 <b>Пользователи</b>\n\n"
        f"📊 Всего: {total}\n"
        f"👑 Администраторов: {len(admins)}\n\n"
        "<b>Список админов:</b>\n"
    )

    for admin in admins:
        text += f"• {admin.full_name}"
        if admin.username:
            text += f" (@{admin.username})"
        text += f" [ID: {admin.telegram_id}]\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("ban"))
async def ban_user_command(
        message: Message,
        user_service: UserService
):
    """
    Заблокировать пользователя.

    Использование: /ban <telegram_id>
    """
    args = message.text.split()

    if len(args) < 2:
        await message.answer(
            "❌ Использование: /ban <telegram_id>\n"
            "Например: /ban 123456789"
        )
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Некорректный ID")
        return

    user = await user_service.get_by_telegram_id(telegram_id)

    if not user:
        await message.answer("❌ Пользователь не найден")
        return

    if user.is_admin:
        await message.answer("❌ Нельзя заблокировать администратора")
        return

    await user_service.ban_user(user.id, ban=True)

    await message.answer(
        f"⛔ Пользователь {user.full_name} заблокирован"
    )


@router.message(Command("unban"))
async def unban_user_command(
        message: Message,
        user_service: UserService
):
    """
    Разблокировать пользователя.

    Использование: /unban <telegram_id>
    """
    args = message.text.split()

    if len(args) < 2:
        await message.answer("❌ Использование: /unban <telegram_id>")
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Некорректный ID")
        return

    user = await user_service.get_by_telegram_id(telegram_id)

    if not user:
        await message.answer("❌ Пользователь не найден")
        return

    await user_service.ban_user(user.id, ban=False)

    await message.answer(
        f"✅ Пользователь {user.full_name} разблокирован"
    )


@router.message(Command("broadcast"))
async def broadcast_command(message: Message):
    """
    Рассылка сообщений всем пользователям.

    Использование: /broadcast <текст сообщения>
    """
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer(
            "❌ Использование: /broadcast <текст сообщения>\n\n"
            "⚠️ Сообщение будет отправлено ВСЕМ пользователям бота!"
        )
        return

    broadcast_text = args[1]

    await message.answer(
        f"📢 <b>Рассылка подготовлена:</b>\n\n"
        f"{broadcast_text}\n\n"
        "⚠️ Функция рассылки требует дополнительной реализации "
        "для работы с большим количеством пользователей.",
        parse_mode="HTML"
    )


@router.message(Command("user"))
async def get_user_info(
        message: Message,
        user_service: UserService,
        ad_service: AdService
):
    """
    Информация о пользователе.

    Использование: /user <telegram_id>
    """
    args = message.text.split()

    if len(args) < 2:
        await message.answer("❌ Использование: /user <telegram_id>")
        return

    try:
        telegram_id = int(args[1])
    except ValueError:
        await message.answer("❌ Некорректный ID")
        return

    user = await user_service.get_by_telegram_id(telegram_id)

    if not user:
        await message.answer("❌ Пользователь не найден")
        return

    ads = await ad_service.get_user_ads(user.id)

    status = []
    if user.is_admin:
        status.append("👑 Админ")
    if user.is_banned:
        status.append("⛔ Заблокирован")

    text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🆔 ID: {user.telegram_id}\n"
        f"📛 Имя: {user.full_name}\n"
        f"📱 Username: @{user.username if user.username else '—'}\n"
        f"📞 Телефон: {user.phone if user.phone else '—'}\n"
        f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n"
        f"📊 Объявлений: {len(ads)}\n"
    )

    if status:
        text += f"\n🏷 Статус: {', '.join(status)}"

    await message.answer(text, parse_mode="HTML")