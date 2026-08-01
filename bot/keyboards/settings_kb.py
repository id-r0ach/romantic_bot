from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.main import SettingsAction, NavAction
from bot.utils.timezone_utils import get_common_timezones


def get_settings_keyboard(notifications_enabled: bool, current_timezone: str = "UTC") -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру с настройками.
    Кнопки переключения уведомлений и выбора часового пояса показывают текущее состояние.
    """
    if notifications_enabled:
        btn_text = "Уведомления: вкл ✅"
    else:
        btn_text = "Уведомления: выкл ❌"

    keyboard = [
        [InlineKeyboardButton(
            text=f"🌍 Часовой пояс: {current_timezone}",
            callback_data=SettingsAction(action="set_timezone").pack()
        )],
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


def get_timezone_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для выбора часового пояса из списка популярных."""
    buttons = []
    
    # Кнопки с популярными поясами
    for tz in get_common_timezones():
        buttons.append([InlineKeyboardButton(
            text=tz,
            callback_data=SettingsAction(action="select_timezone", timezone=tz).pack()
        )])
    
    # Кнопка для ввода произвольного пояса
    buttons.append([InlineKeyboardButton(
        text="✏️ Ввести другой",
        callback_data=SettingsAction(action="other_timezone").pack()
    )])
    
    # Кнопка возврата в настройки
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=NavAction(action="back").pack()
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)