"""
Обработчики поиска объявлений.

Поиск по ключевым словам, категории, местоположению и цене.
"""

from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import SearchStates
from bot.keyboards import (
    get_search_type_keyboard,
    get_cancel_keyboard,
    get_categories_keyboard,
    get_search_results_keyboard,
    get_ad_actions_keyboard,
    get_main_menu
)
from database.models import User, Ad
from services import AdService

router = Router(name="ad_search")


@router.message(Command("search"))
@router.message(F.text == "🔍 Поиск")
async def start_search(message: Message, state: FSMContext):
    """Начало поиска объявлений."""
    await state.clear()
    await state.set_state(SearchStates.select_type)

    await message.answer(
        "🔍 <b>Поиск объявлений</b>\n\n"
        "Выберите способ поиска:",
        reply_markup=get_search_type_keyboard(),
        parse_mode="HTML"
    )


@router.message(SearchStates.select_type, F.text == "🔤 По ключевым словам")
async def search_by_keywords_start(message: Message, state: FSMContext):
    """Поиск по ключевым словам."""
    await state.set_state(SearchStates.waiting_for_keywords)
    await state.update_data(search_type="keywords")

    await message.answer(
        "🔤 Введите <b>ключевые слова</b> для поиска:\n\n"
        "Например: <i>дрель</i>, <i>велосипед</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(SearchStates.waiting_for_keywords)
async def process_keywords(
        message: Message,
        state: FSMContext,
        ad_service: AdService,
        db_user: User
):
    """Обработка ключевых слов."""
    keywords = message.text.strip()

    if len(keywords) < 2:
        await message.answer("❌ Введите хотя бы 2 символа.")
        return

    ads = await ad_service.search(keywords=keywords, limit=50)
    await show_search_results(message, state, ads, db_user, f"🔍 Поиск: {keywords}")


@router.message(SearchStates.select_type, F.text == "📍 По городу")
async def search_by_location_start(message: Message, state: FSMContext):
    """Поиск по местоположению."""
    await state.set_state(SearchStates.waiting_for_location)

    await message.answer(
        "📍 Введите <b>город или район</b>:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(SearchStates.waiting_for_location)
async def process_location_search(
        message: Message,
        state: FSMContext,
        ad_service: AdService,
        db_user: User
):
    """Поиск по местоположению."""
    location = message.text.strip()

    if len(location) < 2:
        await message.answer("❌ Введите хотя бы 2 символа.")
        return

    ads = await ad_service.search(location=location, limit=50)
    await show_search_results(message, state, ads, db_user, f"📍 Место: {location}")


@router.message(SearchStates.select_type, F.text == "🏷 По категории")
async def search_by_category_start(message: Message, state: FSMContext):
    """Поиск по категории."""
    await state.set_state(SearchStates.waiting_for_category)

    await message.answer(
        "🏷 Выберите <b>категорию</b>:",
        reply_markup=get_categories_keyboard(),
        parse_mode="HTML"
    )


@router.message(SearchStates.waiting_for_category)
async def process_category_search(
        message: Message,
        state: FSMContext,
        ad_service: AdService,
        db_user: User
):
    """Поиск по категории."""
    from database.models import AD_CATEGORIES

    if message.text not in AD_CATEGORIES:
        await message.answer("❌ Выберите категорию из списка:")
        return

    ads = await ad_service.search(category=message.text, limit=50)
    await show_search_results(message, state, ads, db_user, f"🏷 {message.text}")


@router.message(SearchStates.select_type, F.text == "💰 По цене")
async def search_by_price_start(message: Message, state: FSMContext):
    """Поиск по цене."""
    await state.set_state(SearchStates.waiting_for_max_price)

    await message.answer(
        "💰 Введите <b>максимальную цену</b> за день:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(SearchStates.waiting_for_max_price)
async def process_price_search(
        message: Message,
        state: FSMContext,
        ad_service: AdService,
        db_user: User
):
    """Поиск по максимальной цене."""
    from utils.validators import validate_price

    price = validate_price(message.text)
    if not price:
        await message.answer("❌ Введите корректную цену.")
        return

    ads = await ad_service.search(max_price=price, limit=50)
    await show_search_results(message, state, ads, db_user, f"💰 До {price:,.0f} ₽/день")


async def show_search_results(
        message: Message,
        state: FSMContext,
        ads: list[Ad],
        db_user: User,
        title: str
):
    """Отображение результатов поиска."""
    await state.update_data(search_results=[ad.id for ad in ads], page=1)
    await state.set_state(SearchStates.show_results)

    if not ads:
        await message.answer(
            f"{title}\n\n📭 <b>Объявления не найдены</b>",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        await state.clear()
        return

    text = f"{title}\n\n📋 <b>Найдено: {len(ads)}</b>\n\n"
    for i, ad in enumerate(ads[:5], 1):
        text += f"{i}. {ad.format_short()}\n\n"

    await message.answer(
        text,
        reply_markup=get_search_results_keyboard(ads, page=1),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("view:ad:"))
async def view_ad_from_search(
        callback: CallbackQuery,
        state: FSMContext,
        ad_service: AdService,
        db_user: User
):
    """Просмотр объявления из поиска."""
    ad_id = int(callback.data.split(":")[2])
    ad = await ad_service.get_by_id(ad_id)

    if not ad:
        await callback.answer("❌ Объявление не найдено", show_alert=True)
        return

    if ad.owner_id != db_user.id:
        await ad_service.increment_views(ad_id)

    keyboard = get_ad_actions_keyboard(ad.id, ad.owner_id, db_user.id)

    if ad.photo_id:
        await callback.message.answer_photo(
            photo=ad.photo_id,
            caption=ad.format_full(),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            ad.format_full(),
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("search:page:"))
async def change_search_page(
        callback: CallbackQuery,
        state: FSMContext,
        ad_service: AdService
):
    """Переключение страницы результатов."""
    page = int(callback.data.split(":")[2])
    data = await state.get_data()
    ad_ids = data.get("search_results", [])

    if not ad_ids:
        await callback.answer("Выполните поиск заново")
        return

    ads = []
    for ad_id in ad_ids:
        ad = await ad_service.get_by_id(ad_id)
        if ad and ad.is_active:
            ads.append(ad)

    await state.update_data(page=page)

    per_page = 5
    start = (page - 1) * per_page
    page_ads = ads[start:start + per_page]

    text = f"🔍 <b>Результаты</b> ({len(ads)})\n\n"
    for i, ad in enumerate(page_ads, start=start + 1):
        text += f"{i}. {ad.format_short()}\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_search_results_keyboard(ads, page=page),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "search:new")
async def new_search(callback: CallbackQuery, state: FSMContext):
    """Новый поиск."""
    await state.clear()
    await state.set_state(SearchStates.select_type)

    await callback.message.answer(
        "🔍 Выберите способ поиска:",
        reply_markup=get_search_type_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ad:contact:"))
async def contact_owner(callback: CallbackQuery, ad_service: AdService):
    """Контакт владельца."""
    ad_id = int(callback.data.split(":")[2])
    ad = await ad_service.get_by_id(ad_id)

    if not ad:
        await callback.answer("❌ Объявление не найдено", show_alert=True)
        return

    owner = ad.owner
    text = f"📞 <b>Контакты</b>\n\n👤 {owner.full_name}\n"

    if owner.username:
        text += f"📱 @{owner.username}\n"

    text += f"📋 {ad.contact_info}\n\n📦 {ad.title}"

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()