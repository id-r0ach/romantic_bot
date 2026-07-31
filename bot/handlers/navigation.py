from aiogram import Router, F
from aiogram.types import Message

from bot.handlers.profile import cmd_profile
from bot.handlers.couple import cmd_couple
from bot.handlers.settings import cmd_settings
from services.user_service import UserService
from services.couple_service import CoupleService

from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.callbacks.main import NavAction
from bot.keyboards.main_kb import get_main_menu_kb

router = Router()


@router.message(F.text == "👤 Профиль")
async def nav_profile(
    message: Message,
    user_service: UserService,
    couple_service: CoupleService,
) -> None:
    """Навигация: показывает профиль."""
    await cmd_profile(message, user_service, couple_service)


@router.message(F.text == "💑 Пара")
async def nav_couple(
    message: Message,
    user_service: UserService,
    couple_service: CoupleService,
) -> None:
    """Навигация: показывает экран пары."""
    await cmd_couple(message, user_service, couple_service)


@router.message(F.text == "⚙️ Настройки")
async def nav_settings(
    message: Message,
    user_service: UserService,
) -> None:
    """Навигация: показывает настройки."""
    await cmd_settings(message, user_service)


@router.callback_query(NavAction.filter(F.action == "back"))
async def cb_back(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Универсальная кнопка 'Назад'.
    1. Сбрасывает FSM (если пользователь был в процессе ввода кода).
    2. Удаляет текущее сообщение с inline-клавиатурой (чтобы не засорять чат).
    3. Показывает главное меню с reply-клавиатурой.
    """
    await state.clear()
    
    # Безопасное удаление сообщения бота
    if callback.message:
        await callback.message.delete()
        
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer()