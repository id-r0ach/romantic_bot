from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from bot.callbacks.main import LetterAction
from bot.keyboards.letter_kb import get_letter_date_keyboard, get_letter_confirm_keyboard
from bot.states.letter import LetterStates
from bot.utils.timezone_utils import to_utc, to_local
from services.couple_service import CoupleService
from services.letter_service import LetterService
from services.user_service import UserService

router = Router()


@router.callback_query(LetterAction.filter(F.action == "select_date"), LetterStates.choosing_date)
async def cb_select_date(
    callback: CallbackQuery,
    state: FSMContext,
    user_service: UserService,
) -> None:
    """Обработка выбора даты открытия письма"""
    callback_data = LetterAction.unpack(callback.data)
    days = callback_data.days
    
    # Получаем часовой пояс пользователя
    user = await user_service.get_profile(telegram_id=callback.from_user.id)
    user_tz = user.timezone if user else "UTC"
    
    # Если выбрана "Своя дата"
    if days is None:
        await state.set_state(LetterStates.entering_date)
        await callback.message.edit_text(
            "🗓 Введи <b>дату</b> открытия в формате <b>ДД.ММ.ГГГГ</b>\n\n"
            "Например: 01.01.2026",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Рассчитываем дату в локальном времени пользователя
    now_local = to_local(datetime.now(timezone.utc), user_tz)
    open_date_local = now_local + timedelta(days=days)
    
    # Конвертируем в UTC для сохранения
    open_date_utc = to_utc(open_date_local, user_tz)
    
    await state.update_data(open_date=open_date_utc.isoformat())
    
    # Переходим сразу к вводу текста
    await state.set_state(LetterStates.entering_text)
    await callback.message.edit_text(
        f"📅 Письмо будет открыто через {days} дней "
        f"({open_date_local.strftime('%d.%m.%Y в %H:%M')})\n\n"
        "Теперь напиши текст письма:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(LetterStates.entering_date, F.text.regexp(r"^\d{2}\.\d{2}\.\d{4}$"))
async def process_entering_date(message: Message, state: FSMContext) -> None:
    """Обработка ввода даты"""
    try:
        # Проверяем, что дата валидна (например, не 32.13.2026)
        datetime.strptime(message.text.strip(), "%d.%m.%Y")
        await state.update_data(date_str=message.text.strip())
        await state.set_state(LetterStates.entering_time)
        await message.answer(
            "⏰ Теперь введи <b>время</b> в формате <b>ЧЧ:ММ</b>\n\n"
            "<i>Формат 24 часа.</i>\n"
            "Например: 12:00",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("Неверная дата. Используй формат <b>ДД.ММ.ГГГГ</b>", parse_mode="HTML")


@router.message(LetterStates.entering_date, ~F.text)
async def process_non_text_date(message: Message) -> None:
    await message.answer("Отправь дату текстом в формате ДД.ММ.ГГГГ")


@router.message(LetterStates.entering_time, F.text.regexp(r"^\d{2}:\d{2}$"))
async def process_entering_time(
    message: Message, 
    state: FSMContext,
    user_service: UserService,
) -> None:
    """Обработка ввода времени и финальная проверка на прошлое"""
    data = await state.get_data()
    date_str = data.get("date_str")
    time_str = message.text.strip()
    
    # Получаем часовой пояс пользователя
    user = await user_service.get_profile(telegram_id=message.from_user.id)
    user_tz = user.timezone if user else "UTC"
    
    try:
        # Объединяем дату и время (считаем их локальным временем пользователя)
        dt_str = f"{date_str} {time_str}"
        date_obj = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
        
        # Конвертируем в UTC
        open_date_utc = to_utc(date_obj, user_tz)
        
        # Проверка на прошлое
        if open_date_utc <= datetime.now(timezone.utc):
            await message.answer("⏳ Дата и время должны быть в будущем. Попробуй указать время позже.")
            return
        
        await state.update_data(open_date=open_date_utc.isoformat())
        await state.set_state(LetterStates.entering_text)
        
        # Для отображения используем локальное время
        open_date_local = to_local(open_date_utc, user_tz)
        
        await message.answer(
            f"📅 Письмо будет открыто <b>{open_date_local.strftime('%d.%m.%Y в %H:%M')}</b>\n\n"
            "Теперь напиши текст письма:",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("Неверное время. Используй формат <b>ЧЧ:ММ</b> (24 часа)", parse_mode="HTML")


@router.message(LetterStates.entering_time, ~F.text)
async def process_non_text_time(message: Message) -> None:
    await message.answer("Отправь время текстом в формате ЧЧ:ММ")


@router.message(LetterStates.entering_text, F.text)
async def process_letter_text(
    message: Message,
    state: FSMContext,
    user_service: UserService,
) -> None:
    """Обработка ввода текста письма"""
    text = message.text.strip()
    
    if not text:
        await message.answer("Напиши что-нибудь ❤️")
        return
    
    if len(text) > 4096:
        await message.answer(f"Слишком длинно. Максимум 4096 символов. Сейчас: {len(text)}")
        return
    
    await state.update_data(text=text)
    await state.set_state(LetterStates.confirming)
    
    data = await state.get_data()
    open_date_str = data.get("open_date")
    
    if not open_date_str:
        await message.answer("Ошибка данных. Начни создание письма заново", reply_markup=get_letter_date_keyboard())
        await state.set_state(LetterStates.choosing_date)
        return
    
    open_date_utc = datetime.fromisoformat(open_date_str)
    
    # Получаем часовой пояс пользователя для отображения
    user = await user_service.get_profile(telegram_id=message.from_user.id)
    user_tz = user.timezone if user else "UTC"
    open_date_local = to_local(open_date_utc, user_tz)
    
    await message.answer(
        f"💌 <b>Подтверждение</b>\n\n"
        f"Дата и время открытия: <b>{open_date_local.strftime('%d.%m.%Y в %H:%M')}</b>\n"
        f"Текст письма:\n\n"
        f"<i>{text}</i>\n\n"
        f"Письмо будет доставлено в указанное время. Изменить нельзя.",
        reply_markup=get_letter_confirm_keyboard(),
        parse_mode="HTML"
    )


@router.message(LetterStates.entering_text, ~F.text)
async def process_non_text(message: Message) -> None:
    await message.answer("Отправь текст письма")


@router.callback_query(LetterAction.filter(F.action == "confirm"), LetterStates.confirming)
async def cb_confirm_letter(
    callback: CallbackQuery,
    state: FSMContext,
    couple_service: CoupleService,
    letter_service: LetterService,
    user_service: UserService,
) -> None:
    """Подтверждение и создание письма"""
    user_id = callback.from_user.id
    data = await state.get_data()
    text = data.get("text")
    open_date_str = data.get("open_date")
    
    if not text or not open_date_str:
        await callback.answer("Ошибка данных. Начни сначала", show_alert=True)
        await state.clear()
        return
    
    open_date_utc = datetime.fromisoformat(open_date_str)
    
    couple = await couple_service.get_couple(user_id)
    if not couple:
        await callback.answer("Ты не в паре", show_alert=True)
        await state.clear()
        return
    
    receiver_id = couple.user2_id if couple.user1_id == user_id else couple.user1_id
    
    await letter_service.create_letter(
        couple_id=couple.id,
        sender_id=user_id,
        receiver_id=receiver_id,
        text=text,
        open_date=open_date_utc
    )
    
    await state.clear()
    
    # Получаем часовой пояс пользователя для отображения
    user = await user_service.get_profile(telegram_id=user_id)
    user_tz = user.timezone if user else "UTC"
    open_date_local = to_local(open_date_utc, user_tz)
    
    await callback.message.edit_text(
        "💌 Письмо запечатано!\n\n"
        f"Оно будет доставлено {open_date_local.strftime('%d.%m.%Y в %H:%M')}.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(LetterAction.filter(F.action == "cancel"))
async def cb_cancel_letter(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена создания письма"""
    await state.clear()
    await callback.message.edit_text("Создание письма отменено", parse_mode="HTML")
    await callback.answer()


@router.message(Command("cancel"), StateFilter(LetterStates))
async def cmd_cancel_letter(message: Message, state: FSMContext) -> None:
    """Отмена через команду /cancel во время FSM"""
    await state.clear()
    await message.answer("Создание письма отменено", parse_mode="HTML")


@router.message(Command("letters"))
async def cmd_show_letters(
    message: Message,
    letter_service: LetterService,
    couple_service: CoupleService,
    user_service: UserService,
) -> None:
    """Показывает все активные (ожидающие доставки) письма пользователя"""
    user_id = message.from_user.id
    
    couple = await couple_service.get_couple(user_id)
    if not couple:
        await message.answer("Ты не в паре. Сначала создай пару 💑", parse_mode="HTML")
        return
    
    # Получаем часовой пояс пользователя
    user = await user_service.get_profile(telegram_id=user_id)
    user_tz = user.timezone if user else "UTC"
    
    letters = await letter_service.get_active_letters(user_id)
    
    if not letters:
        await message.answer(
            "У тебя нет активных писем 💌\n\n"
            "Создай первое письмо через меню пары!",
            parse_mode="HTML"
        )
        return
    
    lines = ["💌 <b>Твои активные письма:</b>\n"]
    for i, letter in enumerate(letters, 1):
        # Конвертируем UTC из БД в локальное время пользователя
        open_date_local = to_local(letter.open_date, user_tz)
        lines.append(
            f"{i}. 📅 {open_date_local.strftime('%d.%m.%Y в %H:%M')}\n"
            f"   <i>{letter.text[:50]}{'...' if len(letter.text) > 50 else ''}</i>"
        )
    
    await message.answer("\n".join(lines), parse_mode="HTML")