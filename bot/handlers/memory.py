from datetime import datetime, timezone

from html import escape

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.callbacks.main import MemoryAction
from bot.keyboards.common_kb import get_cancel_fsm_kb
from bot.keyboards.memory_kb import (
    get_memories_list_kb,
    get_memory_detail_kb,
    get_memory_delete_confirm_kb,
)
from bot.states.memory import MemoryStates
from services.couple_service import CoupleService
from services.memory_service import MemoryService

router = Router()


@router.callback_query(StateFilter(None), MemoryAction.filter(F.action == "list"))
async def cb_show_memories(
    callback: CallbackQuery,
    couple_service: CoupleService,
    memory_service: MemoryService,
) -> None:
    """Показывает список воспоминаний пары."""
    user_id = callback.from_user.id

    couple = await couple_service.get_couple(user_id)

    if not couple:
        await callback.answer("Сначала создай пару 💑", show_alert=True)
        return

    memories = await memory_service.get_memories(couple.id)

    if memories:
        text = (
            "📖 <b>История отношений</b>\n\n"
            "Выбери воспоминание, чтобы посмотреть детали:"
        )
    else:
        text = (
            "📖 <b>История отношений</b>\n\n"
            "Пока нет воспоминаний.\n"
            "Добавьте первое важное событие 💞"
        )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_memories_list_kb(memories),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(StateFilter(None), MemoryAction.filter(F.action == "view"))
async def cb_view_memory(
    callback: CallbackQuery,
    callback_data: MemoryAction,
    couple_service: CoupleService,
    memory_service: MemoryService,
) -> None:
    """Показывает детали воспоминания."""
    user_id = callback.from_user.id
    memory_id = callback_data.memory_id

    if memory_id is None:
        await callback.answer()
        return

    memory = await memory_service.get_memory(memory_id)

    if not memory:
        await callback.answer("Воспоминание не найдено", show_alert=True)
        return

    couple = await couple_service.get_couple(user_id)

    if not couple or couple.id != memory.couple_id:
        await callback.answer("Нет доступа к этому воспоминанию", show_alert=True)
        return

    memory_date = memory.memory_date.strftime("%d.%m.%Y")

    text = (
        f"📖 <b>{escape(memory.title)}</b>\n\n"
        f"📅 <b>Дата события:</b> {memory_date}\n"
    )

    if memory.description:
        text += f"\n{escape(memory.description)}\n"

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_memory_detail_kb(memory.id),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(StateFilter(None), MemoryAction.filter(F.action == "delete"))
async def cb_delete_memory(
    callback: CallbackQuery,
    callback_data: MemoryAction,
    couple_service: CoupleService,
    memory_service: MemoryService,
) -> None:
    """Показывает подтверждение удаления воспоминания."""
    user_id = callback.from_user.id
    memory_id = callback_data.memory_id

    if memory_id is None:
        await callback.answer()
        return

    memory = await memory_service.get_memory(memory_id)

    if not memory:
        await callback.answer("Воспоминание не найдено", show_alert=True)
        return

    couple = await couple_service.get_couple(user_id)

    if not couple or couple.id != memory.couple_id:
        await callback.answer("Нет доступа к этому воспоминанию", show_alert=True)
        return

    text = (
        f"🗑 <b>Удалить воспоминание?</b>\n\n"
        f"<b>{escape(memory.title)}</b>\n"
        f"📅 {memory.memory_date.strftime('%d.%m.%Y')}"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_memory_delete_confirm_kb(memory.id),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(StateFilter(None), MemoryAction.filter(F.action == "delete_yes"))
async def cb_delete_memory_yes(
    callback: CallbackQuery,
    callback_data: MemoryAction,
    couple_service: CoupleService,
    memory_service: MemoryService,
) -> None:
    """Удаляет воспоминание."""
    user_id = callback.from_user.id
    memory_id = callback_data.memory_id

    if memory_id is None:
        await callback.answer()
        return

    memory = await memory_service.get_memory(memory_id)

    if not memory:
        await callback.answer("Воспоминание не найдено", show_alert=True)
        return

    couple = await couple_service.get_couple(user_id)

    if not couple or couple.id != memory.couple_id:
        await callback.answer("Нет доступа к этому воспоминанию", show_alert=True)
        return

    await memory_service.delete_memory(memory_id, user_id)

    memories = await memory_service.get_memories(couple.id)

    if memories:
        text = (
            "📖 <b>История отношений</b>\n\n"
            "Выбери воспоминание, чтобы посмотреть детали:"
        )
    else:
        text = (
            "📖 <b>История отношений</b>\n\n"
            "Пока нет воспоминаний.\n"
            "Добавьте первое важное событие 💞"
        )

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_memories_list_kb(memories),
            parse_mode="HTML",
        )

    await callback.answer("Воспоминание удалено")


@router.callback_query(StateFilter(None), MemoryAction.filter(F.action == "delete_no"))
async def cb_delete_memory_no(
    callback: CallbackQuery,
    callback_data: MemoryAction,
    couple_service: CoupleService,
    memory_service: MemoryService,
) -> None:
    """Отмена удаления, возврат к деталям воспоминания."""
    user_id = callback.from_user.id
    memory_id = callback_data.memory_id

    if memory_id is None:
        await callback.answer()
        return

    memory = await memory_service.get_memory(memory_id)

    if not memory:
        await callback.answer("Воспоминание не найдено", show_alert=True)
        return

    couple = await couple_service.get_couple(user_id)

    if not couple or couple.id != memory.couple_id:
        await callback.answer("Нет доступа к этому воспоминанию", show_alert=True)
        return

    memory_date = memory.memory_date.strftime("%d.%m.%Y")

    text = (
        f"📖 <b>{escape(memory.title)}</b>\n\n"
        f"📅 <b>Дата события:</b> {memory_date}\n"
    )

    if memory.description:
        text += f"\n{escape(memory.description)}\n"

    if callback.message:
        await callback.message.edit_text(
            text,
            reply_markup=get_memory_detail_kb(memory.id),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(StateFilter(None), MemoryAction.filter(F.action == "add"))
async def cb_add_memory(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
) -> None:
    """Запускает FSM добавления воспоминания."""
    user_id = callback.from_user.id

    couple = await couple_service.get_couple(user_id)

    if not couple:
        await callback.answer("Сначала создай пару 💑", show_alert=True)
        return

    await state.set_state(MemoryStates.entering_title)

    await callback.message.answer(
        "📖 <b>Новое воспоминание</b>\n\n"
        "Шаг 1/3.\n"
        "Введи название воспоминания.\n\n"
        "Например:\n"
        "<i>Первое свидание</i>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML",
    )

    await callback.answer()


@router.message(MemoryStates.entering_title, F.text)
async def process_memory_title(message: Message, state: FSMContext) -> None:
    """Обрабатывает название воспоминания."""
    if message.text.startswith("/"):
        return

    title = message.text.strip()

    if not title:
        await message.answer(
            "Введи название.",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML",
        )
        return

    if len(title) > 120:
        await message.answer(
            "Название слишком длинное, максимум 120 символов.",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML",
        )
        return

    await state.update_data(title=title)
    await state.set_state(MemoryStates.entering_description)

    await message.answer(
        "Шаг 2/3.\n"
        "Введи описание воспоминания.\n\n"
        "Если не хочешь добавлять описание, отправь:\n"
        "<code>-</code>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML",
    )


@router.message(MemoryStates.entering_title, ~F.text)
async def process_memory_title_non_text(message: Message) -> None:
    """Если пользователь отправил не текст."""
    await message.answer(
        "Отправь название текстом.",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML",
    )


@router.message(MemoryStates.entering_description, F.text)
async def process_memory_description(message: Message, state: FSMContext) -> None:
    """Обрабатывает описание воспоминания."""
    if message.text.startswith("/"):
        return

    description = message.text.strip()

    if description == "-":
        description = None

    await state.update_data(description=description)
    await state.set_state(MemoryStates.entering_date)

    await message.answer(
        "Шаг 3/3.\n"
        "Введи дату события в формате:\n"
        "<b>ДД.ММ.ГГГГ</b>\n\n"
        "Например:\n"
        "<code>14.02.2026</code>",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML",
    )


@router.message(MemoryStates.entering_description, ~F.text)
async def process_memory_description_non_text(message: Message) -> None:
    """Если пользователь отправил не текст."""
    await message.answer(
        "Отправь описание текстом или <code>-</code>, чтобы пропустить.",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML",
    )


@router.message(MemoryStates.entering_date, F.text)
async def process_memory_date(
    message: Message,
    state: FSMContext,
    couple_service: CoupleService,
    memory_service: MemoryService,
) -> None:
    """Обрабатывает дату воспоминания и создаёт его."""
    if message.text.startswith("/"):
        return

    user_id = message.from_user.id

    try:
        memory_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await message.answer(
            "Неверная дата. Используй формат <b>ДД.ММ.ГГГГ</b>.",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML",
        )
        return

    if memory_date > datetime.now(timezone.utc).date():
        await message.answer(
            "Дата должна быть в прошлом.",
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML",
        )
        return

    couple = await couple_service.get_couple(user_id)

    if not couple:
        await state.clear()
        await message.answer(
            "Сначала создай пару 💑",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()

    title = data.get("title")
    description = data.get("description")

    if not title:
        await state.clear()
        await message.answer(
            "Ошибка данных. Попробуй добавить воспоминание заново.",
            parse_mode="HTML",
        )
        return

    try:
        await memory_service.create_memory(
            couple_id=couple.id,
            author_id=user_id,
            title=title,
            description=description,
            memory_date=memory_date,
        )
    except ValueError as e:
        await message.answer(
            str(e),
            reply_markup=get_cancel_fsm_kb(),
            parse_mode="HTML",
        )
        return

    await state.clear()

    memories = await memory_service.get_memories(couple.id)

    await message.answer(
        "✅ Воспоминание добавлено!",
        parse_mode="HTML",
    )

    await message.answer(
        "📖 <b>История отношений</b>\n\n"
        "Выбери воспоминание, чтобы посмотреть детали:",
        reply_markup=get_memories_list_kb(memories),
        parse_mode="HTML",
    )


@router.message(MemoryStates.entering_date, ~F.text)
async def process_memory_date_non_text(message: Message) -> None:
    """Если пользователь отправил не текст."""
    await message.answer(
        "Отправь дату текстом в формате ДД.ММ.ГГГГ.",
        reply_markup=get_cancel_fsm_kb(),
        parse_mode="HTML",
    )