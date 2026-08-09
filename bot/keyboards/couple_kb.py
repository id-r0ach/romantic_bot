from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.callbacks.main import CoupleAction, NavAction, LetterAction, MemoryAction


def get_couple_main_kb() -> InlineKeyboardMarkup:
    """Клавиатура для пользователя, который НЕ в паре."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🔑 Создать",
                callback_data=CoupleAction(action="create").pack()
            ),
            InlineKeyboardButton(
                text="🔗 Присоединиться",
                callback_data=CoupleAction(action="join").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=NavAction(action="back").pack()
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_couple_in_pair_kb() -> InlineKeyboardMarkup:
    """Клавиатура для пользователя, который УЖЕ в паре."""
    buttons = [
        [
            InlineKeyboardButton(
                text="📖 История",
                callback_data=MemoryAction(action="list").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="💌 Капсула времени",
                callback_data=LetterAction(action="create").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="💔 Выйти из пары",
                callback_data=CoupleAction(action="leave_confirm").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=NavAction(action="back").pack()
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_couple_confirm_leave_kb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения выхода из пары."""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Да, выйти",
                callback_data=CoupleAction(action="leave_yes").pack()
            ),
            InlineKeyboardButton(
                text="❌ Нет, остаться",
                callback_data=CoupleAction(action="leave_no").pack()
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_couple_confirm_leave_final_kb() -> InlineKeyboardMarkup:
    """Клавиатура финального подтверждения выхода из пары."""
    buttons = [
        [
            InlineKeyboardButton(
                text="💔 Да, расстаться",
                callback_data=CoupleAction(action="leave_final_yes").pack()
            ),
            InlineKeyboardButton(
                text="Нет, я передумал",
                callback_data=CoupleAction(action="leave_final_no").pack()
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)