from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.repositories.user import UserRepository
from database.repositories.couple import CoupleRepository
from database.repositories.letter import LetterRepository
from database.repositories.memory import MemoryRepository
from database.repositories.tree import TreeRepository

from services.user_service import UserService
from services.couple_service import CoupleService
from services.letter_service import LetterService
from services.memory_service import MemoryService
from services.tree_service import TreeService


class DbSessionMiddleware(BaseMiddleware):
    """Middleware для управления сессиями БД и проброса сервисов в хэндлеры."""

    def __init__(self, session_pool: async_sessionmaker) -> None:
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            # Репозитории
            user_repo = UserRepository(session)
            couple_repo = CoupleRepository(session)
            letter_repo = LetterRepository(session)
            memory_repo = MemoryRepository(session)
            tree_repo = TreeRepository(session)

            # Bot уже находится в data благодаря aiogram
            bot = data["bot"]

            # Сервисы
            user_service = UserService(user_repo)

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

            couple_service = CoupleService(
                couple_repo,
                letter_service,
                user_repo,
                bot,
            )

            memory_service = MemoryService(
                memory_repo,
                couple_repo,
                tree_service,
            )

            # Пробрасываем зависимости в хэндлеры
            data["session"] = session
            data["user_repo"] = user_repo
            data["user_service"] = user_service
            data["couple_repo"] = couple_repo
            data["couple_service"] = couple_service
            data["letter_service"] = letter_service
            data["memory_repo"] = memory_repo
            data["memory_service"] = memory_service
            data["tree_repo"] = tree_repo
            data["tree_service"] = tree_service

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise