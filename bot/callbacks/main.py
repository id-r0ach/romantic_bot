from aiogram.filters.callback_data import CallbackData
from typing import Literal


class NavAction(CallbackData, prefix="nav"):
    """Навигация по главному меню и общим экранам."""
    action: Literal["back"]


class CoupleAction(CallbackData, prefix="couple"):
    """Действия внутри экрана 'Пара'."""
    action: Literal["create", "join", "leave_confirm", "leave_yes", "leave_no"]


class SettingsAction(CallbackData, prefix="settings"):
    """Действия внутри экрана 'Настройки'."""
    action: Literal["toggle_notifications"]