from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from services.user_service import UserService
from bot.keyboards.settings_kb import get_settings_keyboard

router = Router()


@router.message(Command("settings"))
async def cmd_settings(message: Message, user_service: UserService) -> None:
    """Показывает текущие настройки пользователя."""
    user = await user_service.get_profile(telegram_id=message.from_user.id)
    
    if not user:
        await message.answer("❌ Профиль не найден. Пожалуйста, отправь /start для регистрации.")
        return

    keyboard = get_settings_keyboard(user.notifications)
    
    text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"Здесь ты можешь управлять своими предпочтениями."
    )

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: CallbackQuery, user_service: UserService) -> None:
    """Переключает статус уведомлений."""
    user = await user_service.get_profile(telegram_id=callback.from_user.id)
    
    if not user:
        await callback.answer(" Профиль не найден", show_alert=True)
        return

    # Переключаем статус (True -> False, False -> True)
    new_status = not user.notifications
    
    # Обновляем настройки через сервис
    await user_service.update_settings(
        telegram_id=callback.from_user.id,
        notifications=new_status
    )

    # Обновляем клавиатуру с новым состоянием
    keyboard = get_settings_keyboard(new_status)
    
    # Обновляем сообщение с новой клавиатурой
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    
    # Отвечаем на callback, чтобы убрать "часики"
    status_text = "включены ✅" if new_status else "выключены ❌"
    await callback.answer(f"Уведомления {status_text}")