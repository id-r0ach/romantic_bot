from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database.repositories import UserRepository

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user_repo: UserRepository) -> None:
    # Регистрируем или обновляем пользователя в базе данных
    user, created = await user_repo.get_or_create(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        last_name=message.from_user.last_name,
    )

    if created:
        text = (
            f"Привет, **{user.first_name}**! 👋\n\n"
            f"Добро пожаловать! Твой профиль успешно создан в нашей базе данных."
        )
    else:
        text = (
            f"С возвращением, **{user.first_name}**! 👋\n\n"
            f"Рад снова тебя видеть!"
        )

    await message.answer(text, parse_mode="Markdown")