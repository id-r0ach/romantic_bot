from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.user_service import UserService
from services.couple_service import CoupleService

router = Router()


@router.message(Command("profile"))
async def cmd_profile(
    message: Message,
    user_service: UserService,
    couple_service: CoupleService,
) -> None:
    """Показывает профиль пользователя."""
    user_id = message.from_user.id
    user = await user_service.get_profile(telegram_id=user_id)
    
    if not user:
        await message.answer("❌ Профиль не найден. Пожалуйста, отправь /start для регистрации.")
        return

    couple = await couple_service.get_couple(user_id=user_id)

    notifications_status = "✅ Включены" if user.notifications else "❌ Выключены"
    
    text = (
        f"👤 <b>Твой профиль</b>\n\n"
        f"<b>Имя:</b> {user.first_name}\n"
        f"<b>Username:</b> {user.username or 'не указан'}\n"
        f"<b>Уведомления:</b> {notifications_status}\n\n"
        f"<b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y')}"
    )

    if couple:
        partner_id = couple.user2_id if couple.user1_id == user_id else couple.user1_id
        partner = await user_service.get_profile(partner_id)
        partner_name = (partner.first_name or partner.username or "Неизвестно") if partner else "Неизвестно"
        
        date_str = couple.activated_at.strftime("%d.%m.%Y") if couple.activated_at else "Неизвестно"

        text += (
            f"\n\n💑 <b>В паре с:</b> {partner_name}\n"
            f" <b>Вместе с:</b> {date_str}"
        )
    else:
        text += "\n\n💔 <b>Статус:</b> Не в паре"

    await message.answer(text, parse_mode="HTML")