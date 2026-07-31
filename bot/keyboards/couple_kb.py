from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_couple_main_kb() -> InlineKeyboardMarkup:
    """Главное меню пары: создать или присоединиться"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔑 Создать", callback_data="create_couple"),
        InlineKeyboardButton(text="🔗 Присоединиться", callback_data="join_couple"),
    )
    return builder.as_markup()


def get_couple_confirm_leave_kb() -> InlineKeyboardMarkup:
    """Подтверждение выхода из пары"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да, выйти", callback_data="confirm_leave"),
        InlineKeyboardButton(text="Нет, остаться", callback_data="cancel_leave"),
    )
    return builder.as_markup()


def get_couple_cancel_kb() -> InlineKeyboardMarkup:
    """Кнопка отмены FSM"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Отмена", callback_data="cancel_fsm"),
    )
    return builder.as_markup()