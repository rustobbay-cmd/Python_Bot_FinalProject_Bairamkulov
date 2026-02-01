"""
Обработчики управления объявлениями.

Просмотр, редактирование, удаление своих объявлений.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import AdEditStates, AdDeleteStates
from bot.keyboards import (
    get_my_ads_keyboard,
    get_ad_actions_keyboard,
    get_ad_edit_fields_keyboard,
    get_confirm_delete_keyboard,
    get_cancel_keyboard,
    get_categories_keyboard,
    get_main_menu
)
from database.models import User, AdStatus
from services import AdService

router = Router(name="ad_manage")


@router.message(Command("my_ads"))
@router.message(F.text == "📋 Мои объявления")
async def show_my_ads(
        message: Message,
        state: FSMContext,
        ad_service: AdService,
        db_user: User
):
    """Показать список объявлений пользователя."""
    await state.clear()

    ads = await ad_service.get_user_ads(db_user.id)

    if not ads:
        await message.answer(
            "📭 <b>У вас пока нет объявлений</b>\n\n"
            "Нажмите «📝 Разместить объявление» чтобы создать первое!",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        return

    status_counts = {}
    for ad in ads:
        status_counts[ad.status] = status_counts.get(ad.status, 0) + 1

    stats = "\n".join([
        f"✅ Активных: {status_counts.get(AdStatus.ACTIVE, 0)}",
        f"⏳ На модерации: {status_counts.get(AdStatus.PENDING, 0)}",
        f"🔒 Сданных: {status_counts.get(AdStatus.RENTED, 0)}",
    ])

    await message.answer(
        f"📋 <b>Ваши объявления</b>\n\n{stats}\n\n"
        "Выберите объявление для просмотра:",
        reply_markup=get_my_ads_keyboard(ads),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("myad:view:"))
async def view_my_ad(
        callback: CallbackQuery,
        ad_service: AdService,
        db_user: User
):
    """Просмотр своего объявления."""
    ad_id = int(callback.data.split(":")[2])
    ad = await ad_service.get_by_id(ad_id)

    if not ad or ad.owner_id != db_user.id:
        await callback.answer("❌ Объявление не найдено", show_alert=True)
        return

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


@router.callback_query(F.data.startswith("ad:edit:"))
async def start_edit_ad(
        callback: CallbackQuery,
        state: FSMContext,
        ad_service: AdService,
        db_user: User
):
    """Начало редактирования объявления."""
    ad_id = int(callback.data.split(":")[2])
    ad = await ad_service.get_by_id(ad_id)

    if not ad or ad.owner_id != db_user.id:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    if ad.status == AdStatus.PENDING:
        await callback.answer(
            "⏳ Дождитесь результата модерации",
            show_alert=True
        )
        return

    await state.set_state(AdEditStates.select_field)
    await state.update_data(editing_ad_id=ad_id)

    await callback.message.answer(
        f"✏️ <b>Редактирование:</b> {ad.title}\n\n"
        "Выберите, что хотите изменить:",
        reply_markup=get_ad_edit_fields_keyboard(ad_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit:"), AdEditStates.select_field)
async def select_edit_field(callback: CallbackQuery, state: FSMContext):
    """Выбор поля для редактирования."""
    parts = callback.data.split(":")
    field = parts[1]
    ad_id = int(parts[2])

    if field == "done":
        await state.clear()
        await callback.message.edit_text("✅ Редактирование завершено")
        await callback.answer()
        return

    if field == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Редактирование отменено")
        await callback.answer()
        return

    await state.update_data(editing_field=field)

    field_prompts = {
        "title": ("📝 Введите новое <b>название</b>:", AdEditStates.waiting_for_title),
        "description": ("📋 Введите новое <b>описание</b>:", AdEditStates.waiting_for_description),
        "price": ("💰 Введите новую <b>цену</b> (₽/день):", AdEditStates.waiting_for_price),
        "location": ("📍 Введите новое <b>местоположение</b>:", AdEditStates.waiting_for_location),
        "category": ("🏷 Выберите новую <b>категорию</b>:", AdEditStates.waiting_for_category),
        "contact": ("📞 Введите новый <b>контакт</b>:", AdEditStates.waiting_for_contact),
        "photo": ("📷 Отправьте новое <b>фото</b>:", AdEditStates.waiting_for_photo),
    }

    prompt, new_state = field_prompts.get(field, ("", None))

    if not new_state:
        await callback.answer("Неизвестное поле")
        return

    await state.set_state(new_state)

    if field == "category":
        await callback.message.answer(
            prompt,
            reply_markup=get_categories_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            prompt,
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )

    await callback.answer()


@router.message(AdEditStates.waiting_for_title)
async def edit_title(message: Message, state: FSMContext, ad_service: AdService, db_user: User):
    """Редактирование названия."""
    from utils.validators import validate_title

    title = validate_title(message.text)
    if not title:
        await message.answer("❌ Некорректное название (3-200 символов)")
        return

    await save_edit(message, state, ad_service, db_user, title=title)


@router.message(AdEditStates.waiting_for_description)
async def edit_description(message: Message, state: FSMContext, ad_service: AdService, db_user: User):
    """Редактирование описания."""
    from utils.validators import validate_description

    desc = validate_description(message.text)
    if not desc:
        await message.answer("❌ Некорректное описание (10-2000 символов)")
        return

    await save_edit(message, state, ad_service, db_user, description=desc)


@router.message(AdEditStates.waiting_for_price)
async def edit_price(message: Message, state: FSMContext, ad_service: AdService, db_user: User):
    """Редактирование цены."""
    from utils.validators import validate_price

    price = validate_price(message.text)
    if not price:
        await message.answer("❌ Некорректная цена")
        return

    await save_edit(message, state, ad_service, db_user, price_per_day=price)


@router.message(AdEditStates.waiting_for_location)
async def edit_location(message: Message, state: FSMContext, ad_service: AdService, db_user: User):
    """Редактирование местоположения."""
    from utils.validators import validate_location

    loc = validate_location(message.text)
    if not loc:
        await message.answer("❌ Некорректное местоположение")
        return

    await save_edit(message, state, ad_service, db_user, location=loc)


@router.message(AdEditStates.waiting_for_category)
async def edit_category(message: Message, state: FSMContext, ad_service: AdService, db_user: User):
    """Редактирование категории."""
    from database.models import AD_CATEGORIES

    if message.text not in AD_CATEGORIES:
        await message.answer("❌ Выберите категорию из списка")
        return

    await save_edit(message, state, ad_service, db_user, category=message.text)


@router.message(AdEditStates.waiting_for_contact)
async def edit_contact(message: Message, state: FSMContext, ad_service: AdService, db_user: User):
    """Редактирование контакта."""
    if len(message.text) < 5:
        await message.answer("❌ Контакт слишком короткий")
        return

    await save_edit(message, state, ad_service, db_user, contact_info=message.text)


@router.message(AdEditStates.waiting_for_photo, F.photo)
async def edit_photo(message: Message, state: FSMContext, ad_service: AdService, db_user: User):
    """Редактирование фото."""
    photo_id = message.photo[-1].file_id
    await save_edit(message, state, ad_service, db_user, photo_id=photo_id)


async def save_edit(message: Message, state: FSMContext, ad_service: AdService, db_user: User, **fields):
    """Сохранение изменений."""
    data = await state.get_data()
    ad_id = data.get("editing_ad_id")

    success = await ad_service.update_ad(ad_id, db_user.id, **fields)

    if success:
        await message.answer(
            "✅ Изменения сохранены!\n\n"
            "⏳ Объявление отправлено на повторную модерацию.",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer("❌ Не удалось сохранить изменения")

    await state.clear()


@router.callback_query(F.data.startswith("ad:delete:"))
async def confirm_delete_ad(callback: CallbackQuery, ad_service: AdService, db_user: User):
    """Подтверждение удаления."""
    ad_id = int(callback.data.split(":")[2])
    ad = await ad_service.get_by_id(ad_id)

    if not ad or ad.owner_id != db_user.id:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.answer(
        f"🗑 <b>Удалить объявление?</b>\n\n{ad.title}\n\n"
        "Это действие нельзя отменить!",
        reply_markup=get_confirm_delete_keyboard(ad_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:delete:"))
async def delete_ad(callback: CallbackQuery, ad_service: AdService, db_user: User):
    """Удаление объявления."""
    ad_id = int(callback.data.split(":")[2])

    success = await ad_service.delete_ad(ad_id, db_user.id)

    if success:
        await callback.message.edit_text("✅ Объявление удалено")
    else:
        await callback.message.edit_text("❌ Не удалось удалить")

    await callback.answer()


@router.callback_query(F.data.startswith("confirm:cancel:"))
async def cancel_delete(callback: CallbackQuery):
    """Отмена удаления."""
    await callback.message.edit_text("❌ Удаление отменено")
    await callback.answer()


@router.callback_query(F.data.startswith("ad:rent:"))
async def mark_as_rented(callback: CallbackQuery, ad_service: AdService, db_user: User):
    """Отметить как сданное в аренду."""
    ad_id = int(callback.data.split(":")[2])

    success = await ad_service.set_status(ad_id, db_user.id, AdStatus.RENTED)

    if success:
        await callback.message.answer("🔒 Объявление отмечено как сданное в аренду")
    else:
        await callback.answer("❌ Не удалось изменить статус", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("ad:close:"))
async def close_ad(callback: CallbackQuery, ad_service: AdService, db_user: User):
    """Закрыть объявление."""
    ad_id = int(callback.data.split(":")[2])

    success = await ad_service.set_status(ad_id, db_user.id, AdStatus.CLOSED)

    if success:
        await callback.message.answer("🚫 Объявление закрыто")
    else:
        await callback.answer("❌ Не удалось закрыть", show_alert=True)

    await callback.answer()