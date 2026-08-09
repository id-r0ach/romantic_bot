from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.tree import RelationshipTree
from database.repositories.base import BaseRepository


class TreeRepository(BaseRepository[RelationshipTree]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RelationshipTree, session)

    async def get_by_couple_id(self, couple_id: int) -> RelationshipTree | None:
        """Возвращает дерево пары или None."""
        stmt = (
            select(RelationshipTree)
            .where(RelationshipTree.couple_id == couple_id)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, couple_id: int) -> RelationshipTree:
        """
        Возвращает дерево пары.

        Если дерева ещё нет — создаёт его с XP = 0.
        """
        stmt = (
            pg_insert(RelationshipTree)
            .values(
                couple_id=couple_id,
                xp=0,
            )
            .on_conflict_do_nothing(
                index_elements=[RelationshipTree.couple_id]
            )
            .returning(RelationshipTree)
            .execution_options(populate_existing=True)
        )

        result = await self.session.execute(stmt)
        tree = result.scalar_one_or_none()

        if tree is None:
            tree = await self.get_by_couple_id(couple_id)

        await self.session.flush()

        if tree is None:
            raise ValueError("Не удалось получить или создать дерево")

        return tree

    async def add_xp(self, couple_id: int, amount: int) -> RelationshipTree:
        """
        Добавляет XP дереву пары.

        Если дерева ещё нет, оно будет создано.
        Операция атомарная за счёт ON CONFLICT DO UPDATE.
        """
        stmt = (
            pg_insert(RelationshipTree)
            .values(
                couple_id=couple_id,
                xp=amount,
            )
            .on_conflict_do_update(
                index_elements=[RelationshipTree.couple_id],
                set_={
                    "xp": RelationshipTree.xp + amount,
                },
            )
            .returning(RelationshipTree)
            .execution_options(populate_existing=True)
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.scalar_one()