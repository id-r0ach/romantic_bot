from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.user_service import UserService

router = Router()


@router.message(Command("profile"))
async def cmd_profile(message: Message, user_service: UserService) -> None:
    """Показывает профиль пользователя."""
    user = await user_service.get_profile(telegram_id=message.from_user.id)
    
    if not user:
        await message.answer("❌ Профиль не найден. Пожалуйста, отправь /start для регистрации.")
        return

    # Формируем красивое сообщение с информацией о профиле
    notifications_status = "✅ Включены" if user.notifications else "❌ Выключены"
    
    # Используем HTML вместо Markdown (надежнее)
    text = (
        f"👤 <b>Твой профиль</b>\n\n"
        f"<b>Имя:</b> {user.first_name}\n"
        f"<b>Username:</b> {user.username or 'не указан'}\n"
        f"<b>Часовой пояс:</b> {user.timezone}\n"
        f"<b>Уведомления:</b> {notifications_status}\n\n"
        f"<b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y')}"
    )

    await message.answer(text, parse_mode="HTML")