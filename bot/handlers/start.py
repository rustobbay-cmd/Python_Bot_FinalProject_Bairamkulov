"""
Обработчики стартовых команд.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_main_menu, get_admin_menu
from database.models import User

router = Router(name="start")


WELCOME_MESSAGE = """
🏠 <b>Добро пожаловать в бот аренды вещей!</b>

Здесь вы можете:
- 📝 Размещать объявления о сдаче вещей в аренду
- 🔍 Искать нужные товары для аренды
- 💬 Связываться с владельцами напрямую
- 🔔 Подписываться на уведомления о новых объявлениях

Выберите действие в меню ниже 👇
"""

HELP_MESSAGE = """
📖 <b>Справка по боту</b>

<b>Основные команды:</b>
/start — Главное меню
/help — Эта справка
/new_ad — Создать объявление
/search — Поиск объявлений
/my_ads — Мои объявления
/subscriptions — Мои подписки
/feedback — Обратная связь
"""


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user: User):
    """Обработчик команды /start."""
    await state.clear()
    
    welcome = WELCOME_MESSAGE.replace(
        "Добро пожаловать",
        f"Добро пожаловать, {db_user.full_name}"
    )
    
    keyboard = get_admin_menu() if db_user.is_admin else get_main_menu()
    
    await message.answer(welcome, reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    await message.answer(HELP_MESSAGE, parse_mode="HTML")


@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext, db_user: User):
    """Возврат в главное меню."""
    await state.clear()
    await message.answer(
        "🏠 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "back:main")
async def callback_back_to_main(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Возврат в главное меню через callback."""
    await state.clear()
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext, db_user: User):
    """Отмена текущего действия."""
    await state.clear()
    keyboard = get_admin_menu() if db_user.is_admin else get_main_menu()
    await message.answer("❌ Действие отменено.", reply_markup=keyboard)


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Пустой callback."""
    await callback.answer()