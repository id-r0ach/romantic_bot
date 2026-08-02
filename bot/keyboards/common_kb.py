from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.callbacks.main import NavAction


def get_cancel_fsm_kb() -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру с одной кнопкой [❌ Отмена].
    Используется во всех FSM-состояниях.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=NavAction(action="cancel_fsm").pack())]
        ]
    )