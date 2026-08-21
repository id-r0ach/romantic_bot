import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.callbacks.main import ReasonAction
from bot.keyboards.common_kb import get_cancel_fsm_kb
from bot.keyboards.main_kb import get_main_menu_kb
from bot.keyboards.reason_kb import (
    get_reason_back_kb,
    get_reason_create_kb,
    get_reason_delete_confirm_kb,
    get_reason_draft_kb,
    get_reason_gift_confirm_kb,
    get_reason_recipient_kb,
    get_reason_resume_kb,
)
from bot.states.reason import ReasonStates
from bot.utils.navigation import back_to_main_menu
from services.couple_service import CoupleService
from services.reason_service import ReasonGiftService
from services.tree_service import TreeService
from services.user_service import UserService

logger = logging.getLogger(__name__)

router = Router()


# ==========================================
# ВХОД В АВТОРСКИЙ ПОТОК
# ==========================================

@router.callback_query(ReasonAction.filter(F.action == "author_menu"), StateFilter(None))
async def cb_author_menu(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
    user_service: UserService,
    reason_service: ReasonGiftService,
) -> None:
    """Вход в экран управления подарком для автора."""
    user_id = callback.from_user.id
    couple = await couple_service.get_couple(user_id)
    if not couple:
        await callback.answer("Сначала создай пару 💑", show_alert=True)
        return

    partner_id = couple.user2_id if couple.user1_id == user_id else couple.user1_id
    partner = await user_service.get_profile(partner_id)
    partner_name = (
        (partner.first_name or partner.username or "партнёром")
        if partner
        else "партнёром"
    )

    status = await reason_service.get_author_gift_status(user_id, couple.id)

    if not status:
        # Ничего нет — начинаем новый черновик
        gift = await reason_service.get_or_create_draft(
            author_id=user_id,
            couple_id=couple.id,
            recipient_id=partner_id,
        )

        # Переводим пользователя в FSM, иначе следующий текст не сохранится
        await state.set_state(ReasonStates.waiting_reason)
        await state.update_data(gift_id=gift.id)

        await callback.message.edit_text(
            f"Напиши первую причину, почему ты любишь {partner_name}.\n"
            f"Отправь текстом.\n\n"
            f"💡 Можешь писать по одной причине в день. Черновик сохраняется.",
            reply_markup=get_cancel_fsm_kb(),
        )
        await callback.answer()
        return

    gift, total, opened = status

    if gift.status == "draft":
        await callback.message.edit_text(
            f"У тебя черновик: {total} причин для {partner_name}.\n"
            f"Продолжить?",
            reply_markup=get_reason_resume_kb(),
        )
    elif gift.status == "active":
        await callback.message.edit_text(
            f"Твой подарок активен ❤️\n"
            f"{partner_name} открыл(а) {opened} из {total} причин.",
            reply_markup=get_reason_back_kb(),
        )
    elif gift.status == "finished":
        await callback.message.edit_text(
            f"Прошлый подарок завершён ({total} причин).\n"
            f"Создать новый?",
            reply_markup=get_reason_create_kb(),
        )

    await callback.answer()


# ==========================================
# FSM: НАПИСАНИЕ ПРИЧИН
# ==========================================

@router.callback_query(ReasonAction.filter(F.action == "write"))
async def cb_write_reason(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
    user_service: UserService,
    reason_service: ReasonGiftService,
) -> None:
    """Переход в состояние ввода текста причины."""
    user_id = callback.from_user.id
    couple = await couple_service.get_couple(user_id)
    if not couple:
        await callback.answer("Сначала создай пару 💑", show_alert=True)
        return

    partner_id = couple.user2_id if couple.user1_id == user_id else couple.user1_id
    partner = await user_service.get_profile(partner_id)
    partner_name = (
        (partner.first_name or partner.username or "партнёром")
        if partner
        else "партнёром"
    )

    gift = await reason_service.get_or_create_draft(
        author_id=user_id,
        couple_id=couple.id,
        recipient_id=partner_id,
    )
    total, _ = await reason_service.get_gift_stats(gift.id)

    await state.set_state(ReasonStates.waiting_reason)
    await state.update_data(gift_id=gift.id)

    if total == 0:
        text = (
            f"Напиши первую причину, почему ты любишь {partner_name}.\n"
            f"Отправь текстом.\n\n"
            f"💡 Можешь писать по одной причине в день. Черновик сохраняется."
        )
    else:
        text = f"У тебя уже {total} причин.\nНапиши следующую причину."

    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_cancel_fsm_kb(),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=get_cancel_fsm_kb(),
        )
    await callback.answer()


@router.callback_query(ReasonAction.filter(F.action == "draft_menu"))
async def cb_draft_menu(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
    reason_service: ReasonGiftService,
) -> None:
    """Возврат к экрану черновика без принуждения писать причину."""
    user_id = callback.from_user.id
    couple = await couple_service.get_couple(user_id)
    if not couple:
        await callback.answer("Сначала создай пару 💑", show_alert=True)
        return

    partner_id = couple.user2_id if couple.user1_id == user_id else couple.user1_id
    gift = await reason_service.get_or_create_draft(
        author_id=user_id,
        couple_id=couple.id,
        recipient_id=partner_id,
    )
    total, _ = await reason_service.get_gift_stats(gift.id)

    await state.set_state(ReasonStates.waiting_reason)
    await state.update_data(gift_id=gift.id)

    await callback.message.edit_text(
        f"У тебя {total} причин в черновике.\n"
        f"Можешь написать ещё или подарить.",
        reply_markup=get_reason_draft_kb(),
    )
    await callback.answer()


@router.message(ReasonStates.waiting_reason, F.text)
async def process_reason_text(
    message: Message,
    state: FSMContext,
    reason_service: ReasonGiftService,
) -> None:
    """Сохраняет текстовую причину в черновик."""
    if message.text.startswith("/"):
        return

    data = await state.get_data()
    gift_id = data.get("gift_id")
    if not gift_id:
        await state.clear()
        await message.answer(
            "Ошибка данных. Начни заново.",
            reply_markup=get_main_menu_kb(),
        )
        return

    text = message.text.strip()
    try:
        await reason_service.add_reason(gift_id, text)
        total, _ = await reason_service.get_gift_stats(gift_id)
        await message.answer(
            f"Причина №{total} сохранена ✅",
            reply_markup=get_reason_draft_kb(),
        )
    except ValueError as e:
        await message.answer(str(e))


# ==========================================
# ВРУЧЕНИЕ ПОДАРКА
# ==========================================

@router.callback_query(ReasonAction.filter(F.action == "gift"))
async def cb_gift_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
    reason_service: ReasonGiftService,
) -> None:
    """Показывает подтверждение вручения подарка."""
    data = await state.get_data()
    gift_id = data.get("gift_id")
    
    # Если gift_id нет в state, пытаемся получить активный черновик
    if not gift_id:
        user_id = callback.from_user.id
        couple = await couple_service.get_couple(user_id)
        if couple:
            draft_status = await reason_service.get_draft_status(user_id, couple.id)
            if draft_status:
                gift, _ = draft_status
                gift_id = gift.id
    
    if not gift_id:
        await callback.answer("Ошибка данных. Начни заново.", show_alert=True)
        return

    total, _ = await reason_service.get_gift_stats(gift_id)
    if total < 10:
        await callback.answer(
            f"Нужно минимум 10 причин. Сейчас: {total}",
            show_alert=True,
        )
        return

    try:
        await callback.message.edit_text(
            f"Подарить {total} причин партнёру?\n"
            f"Изменить будет нельзя.",
            reply_markup=get_reason_gift_confirm_kb(),
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(ReasonAction.filter(F.action == "confirm_gift"))
async def cb_confirm_gift(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
    user_service: UserService,
    reason_service: ReasonGiftService,
    tree_service: TreeService,
) -> None:
    """Активирует подарок, начисляет XP и уведомляет получателя."""
    user_id = callback.from_user.id
    data = await state.get_data()
    gift_id = data.get("gift_id")
    
    # Если gift_id нет в state, пытаемся получить активный черновик
    if not gift_id:
        couple = await couple_service.get_couple(user_id)
        if couple:
            draft_status = await reason_service.get_draft_status(user_id, couple.id)
            if draft_status:
                gift, _ = draft_status
                gift_id = gift.id
    
    if not gift_id:
        await callback.answer("Ошибка данных. Начни заново.", show_alert=True)
        await state.clear()
        return

    try:
        gift = await reason_service.activate_gift(gift_id)
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
        return

    couple = await couple_service.get_couple(user_id)
    if not couple:
        await callback.answer("Ты не в паре", show_alert=True)
        await state.clear()
        return

    partner_id = couple.user2_id if couple.user1_id == user_id else couple.user1_id
    partner = await user_service.get_profile(partner_id)
    partner_name = (
        (partner.first_name or partner.username or "партнёру")
        if partner
        else "партнёру"
    )
    user = await user_service.get_profile(user_id)
    user_name = (user.first_name or user.username or "Партнёр") if user else "Партнёр"

    total, _ = await reason_service.get_gift_stats(gift_id)

    # Начисляем XP за вручение подарка
    try:
        await tree_service.add_xp(couple.id, 15, reason="reason_gift_activated")
    except Exception as e:
        logger.error(f"Не удалось начислить XP за подарок: {e}")

    # Уведомляем получателя
    try:
        await callback.message.bot.send_message(
            chat_id=partner_id,
            text=(
                f"{user_name} подарил(а) тебе {total} причин, почему тебя любит ❤️\n"
                f"Каждый день будет открываться одна."
            ),
            reply_markup=get_reason_recipient_kb(can_open=True, next_position=1),
        )
    except Exception as e:
        logger.warning(f"Не удалось уведомить получателя {partner_id}: {e}")

    # Сообщаем автору
    await state.clear()
    try:
        await callback.message.edit_text(
            f"Подарок отправлен ❤️\n"
            f"{partner_name} будет открывать по одной причине в день.",
            reply_markup=get_reason_back_kb(),
        )
    except Exception:
        pass
    await callback.answer()


# ==========================================
# УДАЛЕНИЕ ЧЕРНОВИКА
# ==========================================

@router.callback_query(ReasonAction.filter(F.action == "delete_draft"))
async def cb_delete_draft_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
    reason_service: ReasonGiftService,
) -> None:
    """Показывает подтверждение удаления черновика."""
    data = await state.get_data()
    gift_id = data.get("gift_id")
    
    # Если gift_id нет в state, пытаемся получить активный черновик
    if not gift_id:
        user_id = callback.from_user.id
        couple = await couple_service.get_couple(user_id)
        if couple:
            draft_status = await reason_service.get_draft_status(user_id, couple.id)
            if draft_status:
                gift, _ = draft_status
                gift_id = gift.id
    
    if not gift_id:
        await callback.answer("Ошибка данных. Начни заново.", show_alert=True)
        await state.clear()
        return

    total, _ = await reason_service.get_gift_stats(gift_id)
    try:
        await callback.message.edit_text(
            f"Удалить черновик?\n"
            f"Все {total} причин будут потеряны.",
            reply_markup=get_reason_delete_confirm_kb(),
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(ReasonAction.filter(F.action == "confirm_delete"))
async def cb_confirm_delete(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
    reason_service: ReasonGiftService,
) -> None:
    """Удаляет черновик и все причины."""
    data = await state.get_data()
    gift_id = data.get("gift_id")
    
    # Если gift_id нет в state, пытаемся получить активный черновик
    if not gift_id:
        user_id = callback.from_user.id
        couple = await couple_service.get_couple(user_id)
        if couple:
            draft_status = await reason_service.get_draft_status(user_id, couple.id)
            if draft_status:
                gift, _ = draft_status
                gift_id = gift.id
    
    if not gift_id:
        await callback.answer("Ошибка данных. Начни заново.", show_alert=True)
        await state.clear()
        return

    await reason_service.delete_draft(gift_id)
    await state.clear()
    try:
        await callback.message.edit_text(
            "Черновик удалён.",
            reply_markup=get_reason_back_kb(),
        )
    except Exception:
        pass
    await callback.answer()


# ==========================================
# ОТМЕНА FSM
# ==========================================

@router.callback_query(ReasonAction.filter(F.action == "cancel"))
async def cb_cancel_reason(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Отмена через inline-кнопку. Черновик сохраняется."""
    await state.clear()
    await back_to_main_menu(callback, state)


@router.message(ReasonStates.waiting_reason, Command("cancel"))
async def cmd_cancel_reason(
    message: Message,
    state: FSMContext,
) -> None:
    """Отмена через /cancel. Черновик сохраняется."""
    await state.clear()
    await message.answer(
        "Действие отменено. Черновик сохранён.",
        reply_markup=get_main_menu_kb(),
    )


# ==========================================
# ХЕНДЛЕРЫ ПОЛУЧАТЕЛЯ
# ==========================================

@router.callback_query(ReasonAction.filter(F.action == "recipient_menu"), StateFilter(None))
async def cb_recipient_menu(
    callback: CallbackQuery,
    couple_service: CoupleService,
    user_service: UserService,
    reason_service: ReasonGiftService,
) -> None:
    """Экран получателя: прогресс и кнопка открытия причины."""
    user_id = callback.from_user.id
    couple = await couple_service.get_couple(user_id)
    if not couple:
        await callback.answer("Сначала создай пару 💑", show_alert=True)
        return

    result = await reason_service.get_active_gift_for_recipient(user_id, couple.id)
    if not result:
        await callback.message.edit_text(
            "Пока нет подаренных причин 💌",
            reply_markup=get_reason_back_kb(),
        )
        await callback.answer()
        return

    gift, total, opened = result
    can_open = await reason_service.can_open_today(gift, user_id)
    next_position = opened + 1 if can_open else None

    text = f"💝 Открыто {opened} из {total} причин."
    if not can_open:
        text += "\n\nСегодня ты уже открыл(а) причину. Следующая — завтра ❤️"

    await callback.message.edit_text(
        text,
        reply_markup=get_reason_recipient_kb(can_open=can_open, next_position=next_position),
    )
    await callback.answer()


@router.callback_query(ReasonAction.filter(F.action == "open_reason"))
async def cb_open_reason(
    callback: CallbackQuery,
    couple_service: CoupleService,
    user_service: UserService,
    reason_service: ReasonGiftService,
    tree_service: TreeService,
) -> None:
    """Открывает следующую причину для получателя."""
    user_id = callback.from_user.id
    couple = await couple_service.get_couple(user_id)
    if not couple:
        await callback.answer("Сначала создай пару 💑", show_alert=True)
        return

    result = await reason_service.get_active_gift_for_recipient(user_id, couple.id)
    if not result:
        await callback.answer("Подарок не найден или уже завершён", show_alert=True)
        return

    gift, total, opened = result

    try:
        reason = await reason_service.open_next_reason(gift.id, user_id)
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
        return

    if reason is None:
        # Либо сегодня уже открывал, либо все причины открыты
        new_total, new_opened = await reason_service.get_gift_stats(gift.id)
        if new_opened >= new_total:
            await callback.message.edit_text(
                f"Ты открыл(а) все {new_total} причин! ❤️",
                reply_markup=get_reason_back_kb(),
            )
        else:
            await callback.answer(
                "Сегодня ты уже открыл(а) причину. Следующая — завтра ❤️",
                show_alert=True,
            )
        return

    # Начисляем XP за открытие причины
    try:
        await tree_service.add_xp(couple.id, 1, reason="reason_opened")
    except Exception as e:
        logger.error(f"Не удалось начислить XP за открытие причины: {e}")

    # Показываем причину
    await callback.message.edit_text(
        f"❤️ Причина №{reason.position}\n\n"
        f"«{reason.text}»",
        reply_markup=get_reason_back_kb(),
    )
    await callback.answer()

    # Проверяем, была ли это последняя причина
    new_total, new_opened = await reason_service.get_gift_stats(gift.id)
    if new_opened >= new_total:
        user = await user_service.get_profile(user_id)
        user_name = (user.first_name or user.username or "Партнёр") if user else "Партнёр"

        await callback.message.answer(
            f"🎉 Ты открыл(а) все {new_total} причин! ❤️"
        )

        # Уведомляем автора
        try:
            await callback.message.bot.send_message(
                chat_id=gift.author_id,
                text=f"❤️ {user_name} открыл(а) все твои причины! Подарок завершён.",
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить автора {gift.author_id}: {e}")