from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from services.user_service import UserService
from bot.keyboards.settings_kb import get_settings_keyboard, get_timezone_keyboard
from bot.keyboards.common_kb import get_cancel_fsm_kb
from bot.callbacks.main import SettingsAction
from bot.states.settings import SettingsStates

router = Router()


@router.message(Command("settings"))
async def cmd_settings(message: Message, user_service: UserService) -> None:
    user = await user_service.get_profile(telegram_id=message.from_user.id)
    
    if not user:
        await message.answer("❌ Профиль не найден. Пожалуйста, отправь /start для регистрации.")
        return

    keyboard = get_settings_keyboard(user.notifications, user.timezone or "UTC")
    
    text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"Здесь ты можешь управлять своими предпочтениями."
    )

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(SettingsAction.filter(F.action == "toggle_notifications"))
async def toggle_notifications(callback: CallbackQuery, user_service: UserService) -> None:
    user = await user_service.get_profile(telegram_id=callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return

    new_status = not user.notifications
    
    await user_service.update_settings(
        telegram_id=callback.from_user.id,
        notifications=new_status
    )

    keyboard = get_settings_keyboard(new_status, user.timezone or "UTC")
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    
    status_text = "включены ✅" if new_status else "выключены ❌"
    await callback.answer(f"Уведомления {status_text}")


@router.callback_query(SettingsAction.filter(F.action == "set_timezone"))
async def show_timezone_menu(callback: CallbackQuery) -> None:
    keyboard = get_timezone_keyboard()
    await callback.message.edit_text(
        text="🌍 <b>Выбор часового пояса</b>\n\nВыбери популярный пояс или введи свой:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(SettingsAction.filter(F.action == "select_timezone"))
async def select_timezone(callback: CallbackQuery, callback_data: SettingsAction, user_service: UserService) -> None:
    tz = callback_data.timezone
    try:
        await user_service.update_settings(telegram_id=callback.from_user.id, timezone=tz)
        await callback.answer(f"✅ Пояс {tz} установлен!", show_alert=True)
    except ValueError:
        await callback.answer("❌ Ошибка валидации пояса", show_alert=True)
        return

    user = await user_service.get_profile(telegram_id=callback.from_user.id)
    keyboard = get_settings_keyboard(user.notifications, user.timezone or "UTC")
    await callback.message.edit_text(
        text="⚙️ <b>Настройки</b>\n\nЗдесь ты можешь управлять своими предпочтениями.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(SettingsAction.filter(F.action == "other_timezone"))
async def ask_for_custom_timezone(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        text="✏️ Введи название часового пояса (например, <code>Europe/Berlin</code> или <code>Asia/Tokyo</code>).",
        reply_markup=get_cancel_fsm_kb(),  # <-- ДОБАВЛЕНО
        parse_mode="HTML"
    )
    await state.set_state(SettingsStates.waiting_for_timezone)
    await callback.answer()


@router.message(SettingsStates.waiting_for_timezone)
async def process_custom_timezone(message: Message, state: FSMContext, user_service: UserService) -> None:
    tz_input = message.text.strip()
    
    try:
        await user_service.update_settings(telegram_id=message.from_user.id, timezone=tz_input)
    except ValueError:
        await message.answer(
            "❌ Неверный формат часового пояса. Попробуй еще раз (например, <code>Europe/Paris</code>).",
            reply_markup=get_cancel_fsm_kb(),  # <-- ДОБАВЛЕНО
            parse_mode="HTML"
        )
        return

    await state.clear()
    
    user = await user_service.get_profile(telegram_id=message.from_user.id)
    keyboard = get_settings_keyboard(user.notifications, user.timezone or "UTC")
    
    await message.answer(
        text=f"✅ Часовой пояс <b>{tz_input}</b> успешно установлен!\n\n"
             f"⚙️ <b>Настройки</b>\n\nЗдесь ты можешь управлять своими предпочтениями.",
        parse_mode="HTML",
        reply_markup=keyboard
    )