from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.callbacks.main import LetterListAction


def get_letter_card_kb(letter_id: int) -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру для карточки письма.
    Кнопки: [✏️ Текст] [📅 Дату] [🗑 Отменить]
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Текст",
                    callback_data=LetterListAction(action="edit_text", letter_id=letter_id).pack()
                ),
                InlineKeyboardButton(
                    text="📅 Дату",
                    callback_data=LetterListAction(action="edit_date", letter_id=letter_id).pack()
                ),
                InlineKeyboardButton(
                    text="🗑 Отменить",
                    callback_data=LetterListAction(action="cancel_letter", letter_id=letter_id).pack()
                ),
            ]
        ]
    )