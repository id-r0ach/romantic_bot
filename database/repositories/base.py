from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Базовый асинхронный репозиторий для выполнения CRUD-операций."""

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Получить запись по primary key (id)."""
        return await self.session.get(self.model, id)

    async def get_all(self) -> Sequence[ModelType]:
        """Получить все записи сущности."""
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add(self, entity: ModelType) -> ModelType:
        """Добавить новую сущность в сессию."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Удалить сущность из сессии."""
        await self.session.delete(entity)
        await self.session.flush()