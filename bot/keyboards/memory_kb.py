from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.main import MemoryAction, NavAction
from database.models.memory import Memory


def get_memories_list_kb(memories: list[Memory]) -> InlineKeyboardMarkup:
    """
    Клавиатура списка воспоминаний.

    Каждое воспоминание — отдельная кнопка.
    Внизу кнопка добавить воспоминание и вернуться назад.
    """
    buttons: list[list[InlineKeyboardButton]] = []

    for memory in memories:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=memory.title,
                    callback_data=MemoryAction(
                        action="view",
                        memory_id=memory.id,
                    ).pack(),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="➕ Добавить",
                callback_data=MemoryAction(action="add").pack(),
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


def get_memory_detail_kb(memory_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура детального просмотра воспоминания.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=MemoryAction(
                        action="delete",
                        memory_id=memory_id,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=MemoryAction(action="list").pack(),
                )
            ],
        ]
    )


def get_memory_delete_confirm_kb(memory_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения удаления воспоминания.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=MemoryAction(
                        action="delete_yes",
                        memory_id=memory_id,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Нет, вернуться",
                    callback_data=MemoryAction(
                        action="delete_no",
                        memory_id=memory_id,
                    ).pack(),
                )
            ],
        ]
    )