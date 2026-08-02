from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.callbacks.main import LetterDeliveryAction


def get_letter_delivery_kb(letter_id: int) -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру для доставленного письма.
    Кнопки: [❤️ Спасибо] [💌 Ответить]
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❤️ Спасибо",
                    callback_data=LetterDeliveryAction(action="thanks", letter_id=letter_id).pack()
                ),
                InlineKeyboardButton(
                    text="💌 Ответить",
                    callback_data=LetterDeliveryAction(action="reply", letter_id=letter_id).pack()
                ),
            ]
        ]
    )