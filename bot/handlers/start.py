from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from services.user_service import UserService
from services.couple_service import CoupleService
from bot.keyboards.main_kb import get_main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message, 
    user_service: UserService,
    couple_service: CoupleService
) -> None:
    telegram_id = message.from_user.id
    
    # 1. Получаем или создаем пользователя (UPSERT)
    user = await user_service.get_or_create_user(
        telegram_id=telegram_id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        last_name=message.from_user.last_name,
    )

    # 2. Проверяем наличие пары (используем твой существующий метод get_couple)
    couple = await couple_service.get_couple(telegram_id)

    # 3. Формируем текст приветствия
    text = f"Привет, <b>{user.first_name}</b>! 👋\n\nДобро пожаловать в «Пространство любви»!\n"
    
    if couple:
        # Определяем telegram_id партнёра
        partner_tg_id = couple.user2_id if couple.user1_id == telegram_id else couple.user1_id
        
        # Получаем профиль партнёра
        partner = await user_service.get_profile(partner_tg_id)
        partner_name = (partner.first_name or partner.username or "Партнёр") if partner else "Партнёр"
        
        text += f"Ты уже в паре с {partner_name}. 🥰\nИспользуй меню ниже."
    else:
        text += "Я помогу тебе создать или найти пару.\nИспользуй меню ниже."

    # 4. Отправляем сообщение с reply-клавиатурой
    await message.answer(
        text, 
        parse_mode="HTML",
        reply_markup=get_main_menu_kb()
    )