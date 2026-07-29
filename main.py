import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

from config import settings
from bot.handlers import router


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
)


async def main():
    async with Bot(token=settings.BOT_TOKEN) as bot:
        dp = Dispatcher()

        dp.include_router(router)

        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())