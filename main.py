import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import text

from bot.handlers import router
from bot.middlewares.db import DbSessionMiddleware
from config import settings
from database import async_session_maker, engine

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


async def main() -> None:
    # 1. Проверяем связь с базой данных
    await check_db_connection()

    # 2. Инициализируем хранилище состояний и диспетчер
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # 3. Регистрируем Middleware для всех типов апдейтов
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session_maker))

    # 4. Подключаем роутеры
    dp.include_router(router)

    # 5. Запускаем бота
    async with Bot(token=settings.BOT_TOKEN) as bot:
        try:
            logging.info("Запуск бота...")
            await dp.start_polling(bot)
        finally:
            logging.info("Остановка бота: закрываем пул соединений БД...")
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())