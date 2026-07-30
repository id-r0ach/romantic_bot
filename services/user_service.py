from typing import Optional

from database.models.user import User
from database.repositories.user import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def get_or_create_user(
        self,
        telegram_id: int,
        first_name: str,
        username: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """Получает пользователя или создает/обновляет его при первом взаимодействии (UPSERT)."""
        return await self._user_repo.upsert(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
        )

    async def get_profile(self, telegram_id: int) -> Optional[User]:
        """Получает профиль пользователя по telegram_id."""
        return await self._user_repo.get_by_tg_id(telegram_id)

    async def update_settings(
        self,
        telegram_id: int,
        timezone: Optional[str] = None,
        notifications: Optional[bool] = None,
    ) -> Optional[User]:
        """Обновляет настройки пользователя. Изменяет только переданные не-None значения."""
        return await self._user_repo.update_settings(
            telegram_id=telegram_id,
            timezone=timezone,
            notifications=notifications,
        )