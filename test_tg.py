import asyncio
from aiogram import Bot

from config import settings


async def test():
    bot = Bot(token=settings.BOT_TOKEN)

    webhook = await bot.get_webhook_info()

    print(webhook)

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(test())