from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from services.user_service import UserService

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user_service: UserService) -> None:
    # Получаем пользователя из сервиса (бизнес-логика вынесена)
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        last_name=message.from_user.last_name,
    )

    # Формируем ответное сообщение (только Telegram-логика)
    text = (
        f"Привет, <b>{user.first_name}</b>! 👋\n\n"
        f"Добро пожаловать в «Пространство любви»!\n"
        f"Я помогу тебе укрепить ваши отношения."
    )

    await message.answer(text, parse_mode="HTML")