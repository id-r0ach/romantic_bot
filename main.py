import asyncio
import logging
import sys
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text

from bot.handlers import router
from bot.middlewares.db import DbSessionMiddleware
from config import settings
from database import async_session_maker, engine
from database.repositories.couple import CoupleRepository
from database.repositories.letter import LetterRepository
from database.repositories.memory import MemoryRepository
from database.repositories.tree import TreeRepository
from database.repositories.user import UserRepository
from services.anniversary_service import AnniversaryService
from services.letter_service import LetterService
from services.tree_service import TreeService

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
)


async def check_db_connection() -> None:
    """Проверяет подключение к базе данных через запрос SELECT 1."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logging.info("Успешное подключение к PostgreSQL!")
    except Exception as e:
        logging.critical(f"Ошибка при подключении к базе данных: {e}")
        raise e


async def set_bot_commands(bot: Bot) -> None:
    """Устанавливает команды бота для автодополнения в поле ввода."""
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="couple", description="Управление парой"),
        BotCommand(command="letters", description="Мои активные письма"),
        BotCommand(command="settings", description="Настройки"),
        BotCommand(command="leave", description="Выйти из пары"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
    ]
    await bot.set_my_commands(commands)


async def check_pending_letters(bot: Bot) -> None:
    """Фоновая задача: проверка и доставка писем каждую минуту."""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        couple_repo = CoupleRepository(session)
        letter_repo = LetterRepository(session)
        memory_repo = MemoryRepository(session)
        tree_repo = TreeRepository(session)

        tree_service = TreeService(
            tree_repo,
            couple_repo,
            memory_repo,
            letter_repo,
            bot,
        )

        letter_service = LetterService(
            letter_repo,
            user_repo,
            bot,
            tree_service,
        )

        now = datetime.now(timezone.utc)

        async with session.begin():
            pending_letters = await letter_repo.get_pending(now)

            for letter in pending_letters:
                if letter.status != "pending":
                    continue

                try:
                    await letter_service.deliver_letter(letter)
                    logging.info(f"Письмо {letter.id} успешно доставлено.")
                except Exception as e:
                    logging.error(f"Ошибка при доставке письма {letter.id}: {e}")
                    raise


async def check_anniversaries(bot: Bot) -> None:
    """Фоновая задача: проверка годовщин каждую минуту."""
    async with async_session_maker() as session:
        memory_repo = MemoryRepository(session)
        couple_repo = CoupleRepository(session)

        anniversary_service = AnniversaryService(
            memory_repo,
            couple_repo,
            bot,
        )

        async with session.begin():
            await anniversary_service.check_and_notify(
                datetime.now(timezone.utc)
            )


async def main() -> None:
    await check_db_connection()

    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session_maker))
    dp.include_router(router)

    scheduler = AsyncIOScheduler(timezone="UTC")

    async with Bot(token=settings.BOT_TOKEN) as bot:
        scheduler.add_job(
            check_pending_letters,
            "interval",
            minutes=1,
            kwargs={"bot": bot},
            id="check_pending_letters_job",
            replace_existing=True,
        )

        scheduler.add_job(
            check_anniversaries,
            "interval",
            minutes=1,
            kwargs={"bot": bot},
            id="check_anniversaries_job",
            replace_existing=True,
        )

        scheduler.start()
        logging.info(
            "Планировщик задач запущен: "
            "проверка писем и годовщин каждую минуту."
        )

        try:
            await set_bot_commands(bot)
            logging.info("Запуск бота...")
            await dp.start_polling(bot)
        finally:
            logging.info("Остановка бота: закрываем пул соединений БД и планировщик...")
            scheduler.shutdown()
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())