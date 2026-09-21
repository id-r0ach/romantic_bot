from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.handlers.profile import cmd_profile
from bot.handlers.couple import cmd_couple
from bot.handlers.settings import cmd_settings
from bot.utils.navigation import back_to_main_menu
from bot.callbacks.main import NavAction
from services.user_service import UserService
from services.couple_service import CoupleService

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
    couple_service: CoupleService,
) -> None:
    """Навигация: показывает настройки."""
    await cmd_settings(message, user_service, couple_service)


@router.callback_query(NavAction.filter(F.action == "back"))
async def cb_back(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Универсальная кнопка 'Назад'.
    Делегирует всю логику очистки и возврата в navigation.py
    """
    await back_to_main_menu(callback, state)


@router.callback_query(NavAction.filter(F.action == "cancel_fsm"))
async def cb_cancel_fsm(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Универсальная отмена FSM-процесса.
    Сбрасывает состояние и возвращает в главное меню.
    """
    await back_to_main_menu(callback, state)