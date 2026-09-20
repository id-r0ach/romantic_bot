from typing import Literal

from aiogram.filters.callback_data import CallbackData


class NavAction(CallbackData, prefix="nav"):
    """Навигация по главному меню и общим экранам."""
    action: Literal["back", "cancel_fsm"]


class CoupleAction(CallbackData, prefix="couple"):
    """Действия внутри экрана 'Пара'."""
    action: Literal[
        "create",
        "join",
        "leave_confirm",
        "leave_yes",
        "leave_no",
        "leave_final_yes",
        "leave_final_no",
    ]


class SettingsAction(CallbackData, prefix="settings"):
    """Действия внутри экрана 'Настройки'."""
    action: Literal[
        "toggle_notifications",
        "set_timezone",
        "select_timezone",
        "other_timezone",
        "set_anniversary_time",
        "set_time_08",
        "set_time_09",
        "set_time_10",
        "set_time_11",
        "set_time_custom",
    ]
    timezone: str | None = None


class LetterAction(CallbackData, prefix="letter"):
    """Действия с капсулой времени."""
    action: Literal["create", "select_date", "confirm", "cancel"]
    days: int | None = None  # 7, 30, 365 или None для "Своя дата"


class LetterDeliveryAction(CallbackData, prefix="delivery"):
    """Действия с доставленным письмом."""
    action: Literal["thanks", "reply"]
    letter_id: int


class LetterListAction(CallbackData, prefix="letter_list"):
    """Действия с письмом из списка /letters."""
    action: Literal["edit_text", "edit_date", "cancel_letter"]
    letter_id: int


class MemoryAction(CallbackData, prefix="memory"):
    """Действия внутри экрана 'История'."""
    action: Literal[
        "list",
        "add",
        "view",
        "delete",
        "delete_yes",
        "delete_no",
    ]
    memory_id: int | None = None


class TreeAction(CallbackData, prefix="tree"):
    """Действия внутри экрана дерева."""
    action: Literal["show"]


class ReasonAction(CallbackData, prefix="reason"):
    """Действия внутри подарка '100 причин'."""
    action: Literal[
        "author_menu",
        "recipient_menu",
        "write",
        "draft_menu",
        "gift",
        "delete_draft",
        "confirm_gift",
        "confirm_delete",
        "open_reason",
        "cancel",
    ]