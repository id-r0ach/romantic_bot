import re
from datetime import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from services.user_service import UserService
from services.couple_service import CoupleService
from bot.keyboards.settings_kb import get_settings_keyboard, get_timezone_keyboard, get_anniversary_time_keyboard
from bot.keyboards.common_kb import get_cancel_fsm_kb
from bot.keyboards.couple_kb import get_couple_main_kb
from bot.callbacks.main import SettingsAction
from bot.states.settings import SettingsStates

router = Router()


@router.callback_query(SettingsAction.filter(F.action == "back_to_settings"))
async def back_to_settings(callback: CallbackQuery, user_service: UserService, couple_service: CoupleService) -> None:
    user = await user_service.get_profile(telegram_id=callback.from_user.id)

    if not user:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return

    couple = await couple_service.get_couple(user_id=callback.from_user.id)
    current_time = couple.anniversary_time.strftime("%H:%M") if couple and couple.anniversary_time else None

    keyboard = get_settings_keyboard(user.notifications, user.timezone or "UTC", current_time)

    text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"Здесь ты можешь управлять своими предпочтениями."
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@router.message(Command("settings"))
async def cmd_settings(message: Message, user_service: UserService, couple_service: CoupleService) -> None:
    user = await user_service.get_profile(telegram_id=message.from_user.id)
    
    if not user:
        await message.answer("❌ Профиль не найден. Пожалуйста, отправь /start для регистрации.")
        return

    couple = await couple_service.get_couple(user_id=message.from_user.id)
    current_time = couple.anniversary_time.strftime("%H:%M") if couple and couple.anniversary_time else None

    keyboard = get_settings_keyboard(user.notifications, user.timezone or "UTC", current_time)
    
    text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"Здесь ты можешь управлять своими предпочтениями."
    )

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(SettingsAction.filter(F.action == "toggle_notifications"))
async def toggle_notifications(callback: CallbackQuery, user_service: UserService, couple_service: CoupleService) -> None:
    user = await user_service.get_profile(telegram_id=callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Профиль не найден", show_alert=True)
        return

    new_status = not user.notifications
    
    await user_service.update_settings(
        telegram_id=callback.from_user.id,
        notifications=new_status
    )

    couple = await couple_service.get_couple(user_id=callback.from_user.id)
    current_time = couple.anniversary_time.strftime("%H:%M") if couple and couple.anniversary_time else None

    keyboard = get_settings_keyboard(new_status, user.timezone or "UTC", current_time)
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
async def select_timezone(callback: CallbackQuery, callback_data: SettingsAction, user_service: UserService, couple_service: CoupleService) -> None:
    tz = callback_data.timezone
    try:
        await user_service.update_settings(telegram_id=callback.from_user.id, timezone=tz)
        await callback.answer(f"✅ Пояс {tz} установлен!", show_alert=True)
    except ValueError:
        await callback.answer("❌ Ошибка валидации пояса", show_alert=True)
        return

    user = await user_service.get_profile(telegram_id=callback.from_user.id)
    couple = await couple_service.get_couple(user_id=callback.from_user.id)
    current_time = couple.anniversary_time.strftime("%H:%M") if couple and couple.anniversary_time else None

    keyboard = get_settings_keyboard(user.notifications, user.timezone or "UTC", current_time)
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
async def process_custom_timezone(message: Message, state: FSMContext, user_service: UserService, couple_service: CoupleService) -> None:
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
    couple = await couple_service.get_couple(user_id=message.from_user.id)
    current_time = couple.anniversary_time.strftime("%H:%M") if couple and couple.anniversary_time else None
    keyboard = get_settings_keyboard(user.notifications, user.timezone or "UTC", current_time)
    
    await message.answer(
        text=f"✅ Часовой пояс <b>{tz_input}</b> успешно установлен!\n\n"
             f"⚙️ <b>Настройки</b>\n\nЗдесь ты можешь управлять своими предпочтениями.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(SettingsAction.filter(F.action == "set_anniversary_time"))
async def show_anniversary_time_menu(callback: CallbackQuery, couple_service: CoupleService) -> None:
    couple = await couple_service.get_couple(user_id=callback.from_user.id)
    if not couple:
        await callback.message.edit_text(
            text="Сначала создай пару 💑",
            reply_markup=get_couple_main_kb()
        )
        await callback.answer()
        return

    keyboard = get_anniversary_time_keyboard()
    await callback.message.edit_text(
        text="⏰ <b>Выбор времени напоминаний</b>\n\nВыбери одно из предложенных или введи своё (ЧЧ:ММ):",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(SettingsAction.filter(F.action.in_({"set_time_08", "set_time_09", "set_time_10", "set_time_11"})))
async def select_preset_anniversary_time(callback: CallbackQuery, callback_data: SettingsAction, user_service: UserService, couple_service: CoupleService) -> None:
    action_to_time = {
        "set_time_08": time(8, 0),
        "set_time_09": time(9, 0),
        "set_time_10": time(10, 0),
        "set_time_11": time(11, 0),
    }
    new_time = action_to_time[callback_data.action]
    try:
        await couple_service.update_anniversary_time(user_id=callback.from_user.id, new_time=new_time)
    except ValueError as e:
        await callback.answer(f"❌ {e}", show_alert=True)
        return

    user = await user_service.get_profile(telegram_id=callback.from_user.id)
    couple = await couple_service.get_couple(user_id=callback.from_user.id)
    current_time_str = couple.anniversary_time.strftime("%H:%M") if couple and couple.anniversary_time else None

    keyboard = get_settings_keyboard(user.notifications, user.timezone or "UTC", current_time_str)

    await callback.message.edit_text(
        text=f"✅ Время напоминаний изменено на {new_time.strftime('%H:%M')}\n\n"
             f"⚙️ <b>Настройки</b>\n\nЗдесь ты можешь управлять своими предпочтениями.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(SettingsAction.filter(F.action == "set_time_custom"))
async def ask_for_custom_time(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        text="✏️ Введи время в формате ЧЧ:ММ (например, 14:30):",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )
    await state.set_state(SettingsStates.waiting_for_anniversary_time)
    await callback.answer()


@router.message(SettingsStates.waiting_for_anniversary_time, F.text.regexp(r'^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$'))
async def process_custom_anniversary_time(message: Message, state: FSMContext, user_service: UserService, couple_service: CoupleService) -> None:
    time_str = message.text.strip()
    hour, minute = map(int, time_str.split(':'))
    new_time = time(hour, minute)

    try:
        await couple_service.update_anniversary_time(user_id=message.from_user.id, new_time=new_time)
    except ValueError as e:
        await message.answer(f"❌ {e}")
        await state.clear()
        return

    await state.clear()

    user = await user_service.get_profile(telegram_id=message.from_user.id)
    couple = await couple_service.get_couple(user_id=message.from_user.id)
    current_time_str = couple.anniversary_time.strftime("%H:%M") if couple and couple.anniversary_time else None

    keyboard = get_settings_keyboard(user.notifications, user.timezone or "UTC", current_time_str)

    await message.answer(
        text=f"✅ Время напоминаний изменено на {time_str}\n\n"
             f"⚙️ <b>Настройки</b>\n\nЗдесь ты можешь управлять своими предпочтениями.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message(SettingsStates.waiting_for_anniversary_time)
async def process_invalid_custom_time(message: Message) -> None:
    await message.answer(
        text="❌ Неверный формат. Пожалуйста, введите время в формате ЧЧ:ММ (например, 14:30).",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML"
    )