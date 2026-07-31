from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.main import SettingsAction, NavAction


def get_settings_keyboard(notifications_enabled: bool) -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру с настройками.
    Кнопка переключения уведомлений показывает текущее состояние.
    """
    # Иконка и текст зависят от текущего состояния
    if notifications_enabled:
        btn_text = "Уведомления: вкл ✅"
    else:
        btn_text = "Уведомления: выкл ❌"

    keyboard = [
        [InlineKeyboardButton(
            text=btn_text,
            callback_data=SettingsAction(action="toggle_notifications").pack()
        )],
        [InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=NavAction(action="back").pack()
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)