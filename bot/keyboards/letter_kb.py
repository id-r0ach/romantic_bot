from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.main import LetterAction


def get_letter_date_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора даты открытия письма."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Через неделю",
                    callback_data=LetterAction(action="select_date", days=7).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Через месяц",
                    callback_data=LetterAction(action="select_date", days=30).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Через год",
                    callback_data=LetterAction(action="select_date", days=365).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗓 Своя дата",
                    callback_data=LetterAction(action="select_date", days=None).pack()
                )
            ],
        ]
    )


def get_letter_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения отправки письма."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отправить",
                    callback_data=LetterAction(action="confirm").pack()
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=LetterAction(action="cancel").pack()
                )
            ]
        ]
    )