from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с таблицей пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_tg_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по внутреннему ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        telegram_id: int,
        first_name: str,
        username: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """
        Атомарный UPSERT через PostgreSQL ON CONFLICT.
        Если пользователя нет — создает. Если есть — обновляет имя.
        """
        stmt = (
            pg_insert(User)
            .values(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            .on_conflict_do_update(
                index_elements=[User.telegram_id],
                set_={
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            .returning(User)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update_settings(
        self,
        telegram_id: int,
        timezone: Optional[str] = None,
        notifications: Optional[bool] = None,
    ) -> Optional[User]:
        """
        Обновляет только переданные настройки.
        Изменения зафиксирует DbSessionMiddleware при коммите.
        """
        user = await self.get_by_tg_id(telegram_id)
        if not user:
            return None

        if timezone is not None:
            user.timezone = timezone
        if notifications is not None:
            user.notifications = notifications

        return user