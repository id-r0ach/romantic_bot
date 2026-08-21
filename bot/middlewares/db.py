from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.repositories.couple import CoupleRepository
from database.repositories.letter import LetterRepository
from database.repositories.memory import MemoryRepository
from database.repositories.reason import ReasonGiftRepository, ReasonRepository
from database.repositories.tree import TreeRepository
from database.repositories.user import UserRepository
from services.couple_service import CoupleService
from services.letter_service import LetterService
from services.memory_service import MemoryService
from services.reason_service import ReasonGiftService
from services.tree_service import TreeService
from services.user_service import UserService


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

            # Новые репозитории для подарка "100 причин"
            reason_gift_repo = ReasonGiftRepository(session)
            reason_repo = ReasonRepository(session)

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

            reason_service = ReasonGiftService(
                reason_gift_repo=reason_gift_repo,
                reason_repo=reason_repo,
                user_repo=user_repo,
            )

            couple_service = CoupleService(
                couple_repo=couple_repo,
                letter_service=letter_service,
                user_repo=user_repo,
                bot=bot,
                reason_service=reason_service,
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

            # Новые зависимости для подарка "100 причин"
            data["reason_gift_repo"] = reason_gift_repo
            data["reason_repo"] = reason_repo
            data["reason_service"] = reason_service

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise