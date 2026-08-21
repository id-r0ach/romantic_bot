from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.main import NavAction, ReasonAction


def get_reason_write_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура для состояния ввода причины.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=ReasonAction(action="cancel").pack(),
                )
            ]
        ]
    )


def get_reason_draft_kb() -> InlineKeyboardMarkup:
    """
    Экран черновика после сохранения причины.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Написать ещё",
                    callback_data=ReasonAction(action="write").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Подарить",
                    callback_data=ReasonAction(action="gift").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить черновик",
                    callback_data=ReasonAction(action="delete_draft").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=ReasonAction(action="cancel").pack(),
                )
            ],
        ]
    )


def get_reason_resume_kb() -> InlineKeyboardMarkup:
    """
    Если у автора уже есть черновик.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Продолжить",
                    callback_data=ReasonAction(action="write").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Подарить",
                    callback_data=ReasonAction(action="gift").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить черновик",
                    callback_data=ReasonAction(action="delete_draft").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=NavAction(action="back").pack(),
                )
            ],
        ]
    )

def get_reason_create_kb() -> InlineKeyboardMarkup:
    """
    Если прошлый подарок завершён и можно создать новый.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать",
                    callback_data=ReasonAction(action="write").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=NavAction(action="back").pack(),
                )
            ],
        ]
    )


def get_reason_gift_confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение вручения подарка."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подарить",
                    callback_data=ReasonAction(action="confirm_gift").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Назад",
                    callback_data=ReasonAction(action="draft_menu").pack(),
                )
            ],
        ]
    )


def get_reason_delete_confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение удаления черновика."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить",
                    callback_data=ReasonAction(action="confirm_delete").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Нет, оставить",
                    callback_data=ReasonAction(action="draft_menu").pack(),
                )
            ],
        ]
    )


def get_reason_recipient_kb(
    can_open: bool,
    next_position: int | None = None,
) -> InlineKeyboardMarkup:
    """
    Экран получателя.
    Если сегодня можно открыть причину — показываем кнопку открытия.
    """
    buttons: list[list[InlineKeyboardButton]] = []

    if can_open:
        if next_position is not None:
            text = f"💌 Открыть причину №{next_position}"
        else:
            text = "💌 Открыть причину"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=ReasonAction(action="open_reason").pack(),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=NavAction(action="back").pack(),
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_reason_back_kb() -> InlineKeyboardMarkup:
    """
    Простой возврат назад.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=NavAction(action="back").pack(),
                )
            ]
        ]
    )