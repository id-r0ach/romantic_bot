from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_kb import get_main_menu_kb
from bot.keyboards.couple_kb import get_couple_main_kb, get_couple_in_pair_kb, get_couple_confirm_leave_kb
from bot.callbacks.main import CoupleAction
from bot.states.couple import CoupleStates
from services.couple_service import CoupleService
from services.user_service import UserService

router = Router()


@router.message(Command("couple"))
async def cmd_couple(
    message: Message,
    user_service: UserService,
    couple_service: CoupleService,
) -> None:
    """Обработка команды /couple"""
    user_id = message.from_user.id
    couple = await couple_service.get_couple(user_id)
    
    if couple:
        partner_id = couple.user2_id if couple.user1_id == user_id else couple.user1_id
        partner = await user_service.get_profile(partner_id)
        partner_name = (partner.first_name or partner.username or "твоим партнёром") if partner else "твоим партнёром"
        
        await message.answer(
            f"Ты уже в паре с {partner_name} ❤️",
            reply_markup=get_couple_in_pair_kb(),
            parse_mode="HTML"
        )
        return
    
    await message.answer(
        "Ты сейчас не в паре. Что хочешь сделать?",
        reply_markup=get_couple_main_kb(),
        parse_mode="HTML"
    )


@router.callback_query(CoupleAction.filter(F.action == "create"))
async def cb_create_couple(
    callback: CallbackQuery,
    couple_service: CoupleService,
) -> None:
    """Обработка нажатия на кнопку 'Создать пару'"""
    user_id = callback.from_user.id
    
    try:
        couple = await couple_service.create_couple(user_id)
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
        return
    
    # Показываем время в UTC
    expires_at = couple.invite_expires.strftime("%d.%m.%Y %H:%M")
    
    await callback.message.answer(
        f"🔑 Твой код приглашения:\n\n"
        f"<b>{couple.invite_code}</b>\n\n"
        f"Действует до {expires_at} (UTC, 24 часа).\n"
        f"Отправь его партнёру, чтобы он мог присоединиться.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(CoupleAction.filter(F.action == "join"))
async def cb_join_couple(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
) -> None:
    """Обработка нажатия на кнопку 'Присоединиться'"""
    user_id = callback.from_user.id
    
    existing = await couple_service.get_couple(user_id)
    if existing:
        await callback.answer("Сначала выйди из текущей пары", show_alert=True)
        return

    await state.set_state(CoupleStates.waiting_for_code)
    await callback.message.answer(
        "Введи код приглашения (или нажми /cancel):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(CoupleStates.waiting_for_code, Command("couple"))
async def cmd_couple_in_fsm(message: Message, state: FSMContext) -> None:
    """Если пользователь написал /couple во время ввода кода, сбрасываем FSM"""
    await state.clear()
    await message.answer(
        "Действие отменено. Теперь ты можешь создать пару или присоединиться к другой.",
        parse_mode="HTML"
    )


@router.message(CoupleStates.waiting_for_code, F.text)
async def process_join_code(
    message: Message,
    state: FSMContext,
    couple_service: CoupleService,
    user_service: UserService,
) -> None:
    """Обработка введённого кода"""
    if message.text.startswith('/'):
        return
    
    user_id = message.from_user.id
    code = message.text.strip().upper()

    try:
        couple = await couple_service.join_couple(user_id, code)
    except ValueError as e:
        if "уже в паре" in str(e):
            await state.clear()
        await message.answer(str(e), parse_mode="HTML")
        return

    await state.clear()
    
    user2 = await user_service.get_profile(user_id)
    user1 = await user_service.get_profile(couple.user1_id)
    
    user2_name = user2.first_name or user2.username or "твоим партнёром"
    user1_name = user1.first_name or user1.username or "твоим партнёром"
    
    await message.answer(
        f"❤️ Вы теперь пара с {user1_name}!",
        parse_mode="HTML"
    )
    
    await message.bot.send_message(
        chat_id=couple.user1_id,
        text=f"❤️ {user2_name} присоединился к тебе! Вы теперь пара!",
        parse_mode="HTML"
    )


@router.message(CoupleStates.waiting_for_code, ~F.text)
async def process_non_text_in_fsm(message: Message) -> None:
    """Если пользователь отправил фото/стикер вместо текста"""
    await message.answer(
        "Отправь код текстом (или нажми /cancel).",
        parse_mode="HTML"
    )


@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Отмена текущего действия и сброс FSM"""
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_menu_kb(),
        parse_mode="HTML"
    )


@router.message(Command("leave"))
async def cmd_leave(
    message: Message,
    couple_service: CoupleService,
) -> None:
    """Обработка команды /leave"""
    user_id = message.from_user.id
    couple = await couple_service.get_couple(user_id)
    
    if not couple:
        await message.answer("Ты не в паре.", parse_mode="HTML")
        return
        
    await message.answer(
        "Ты уверен, что хочешь выйти из пары?",
        reply_markup=get_couple_confirm_leave_kb(),
        parse_mode="HTML"
    )


@router.callback_query(CoupleAction.filter(F.action == "leave_confirm"))
async def cb_confirm_leave(
    callback: CallbackQuery,
    couple_service: CoupleService,
) -> None:
    """Показывает подтверждение выхода из пары"""
    user_id = callback.from_user.id
    
    couple = await couple_service.get_couple(user_id)
    if not couple:
        await callback.answer("Ты не в паре.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "Ты уверен, что хочешь выйти из пары?",
        reply_markup=get_couple_confirm_leave_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(CoupleAction.filter(F.action == "leave_yes"))
async def cb_leave_yes(
    callback: CallbackQuery,
    couple_service: CoupleService,
    user_service: UserService,
    state: FSMContext,
) -> None:
    """Подтверждение выхода из пары"""
    user_id = callback.from_user.id
    
    couple = await couple_service.get_couple(user_id)
    if not couple:
        await callback.answer("Ты не в паре.", show_alert=True)
        return
    
    partner_id = couple.user2_id if couple.user1_id == user_id else couple.user1_id
    
    try:
        await couple_service.leave_couple(user_id)
        await state.clear()
        
        await callback.message.edit_text("Ты вышел из пары. 😔", parse_mode="HTML")
        
        user = await user_service.get_profile(user_id)
        user_name = user.first_name or user.username or "Твой партнёр"
        
        await callback.message.bot.send_message(
            chat_id=partner_id,
            text=f"😔 {user_name} вышел из пары.",
            parse_mode="HTML"
        )
    except ValueError:
        await callback.answer("Ты не в паре.", show_alert=True)


@router.callback_query(CoupleAction.filter(F.action == "leave_no"))
async def cb_leave_no(callback: CallbackQuery) -> None:
    """Отмена выхода из пары"""
    await callback.message.edit_text("Хорошо, остаёмся вместе! ❤️", parse_mode="HTML")
    await callback.answer()