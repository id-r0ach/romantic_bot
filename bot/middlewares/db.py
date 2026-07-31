from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.repositories.user import UserRepository
from database.repositories.couple import CoupleRepository
from services.user_service import UserService
from services.couple_service import CoupleService


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
            # Создаем репозитории
            user_repo = UserRepository(session)
            couple_repo = CoupleRepository(session)
            
            # Создаем сервисы с внедренными зависимостями
            user_service = UserService(user_repo)
            couple_service = CoupleService(couple_repo)
            
            # Пробрасываем сессию и сервисы в data
            data["session"] = session
            data["user_repo"] = user_repo
            data["user_service"] = user_service
            data["couple_repo"] = couple_repo
            data["couple_service"] = couple_service

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise