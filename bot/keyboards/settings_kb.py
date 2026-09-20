from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.main import SettingsAction, NavAction
from bot.utils.timezone_utils import get_common_timezones


def get_settings_keyboard(notifications_enabled: bool, current_timezone: str = "UTC", current_time: str | None = None) -> InlineKeyboardMarkup:
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
        )]
    ]
    
    time_text = current_time if current_time else "Не задано"
    keyboard.append([InlineKeyboardButton(
        text=f"⏰ Время напоминаний: {time_text}",
        callback_data=SettingsAction(action="set_anniversary_time").pack()
    )])

    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=NavAction(action="back").pack()
    )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_anniversary_time_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для выбора времени напоминаний."""
    keyboard = [
        [
            InlineKeyboardButton(text="08:00", callback_data=SettingsAction(action="set_time_08").pack()),
            InlineKeyboardButton(text="09:00", callback_data=SettingsAction(action="set_time_09").pack()),
        ],
        [
            InlineKeyboardButton(text="10:00", callback_data=SettingsAction(action="set_time_10").pack()),
            InlineKeyboardButton(text="11:00", callback_data=SettingsAction(action="set_time_11").pack()),
        ],
        [
            InlineKeyboardButton(text="📝 Своё время", callback_data=SettingsAction(action="set_time_custom").pack())
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=SettingsAction(action="back_to_settings").pack())
        ]
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