from datetime import date

from sqlalchemy import delete as sa_delete
from sqlalchemy import extract, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.couple import Couple
from database.models.memory import Memory
from database.repositories.base import BaseRepository


class MemoryRepository(BaseRepository[Memory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Memory, session)

    async def create(self, memory: Memory) -> Memory:
        """Создаёт воспоминание."""
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def get_by_couple(self, couple_id: int) -> list[Memory]:
        """Возвращает воспоминания пары, отсортированные по дате события."""
        stmt = (
            select(Memory)
            .where(Memory.couple_id == couple_id)
            .order_by(Memory.memory_date.desc(), Memory.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_id(self, memory_id: int) -> None:
        """Удаляет воспоминание по ID."""
        stmt = sa_delete(Memory).where(Memory.id == memory_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def exists_by_title_and_date(
        self,
        couple_id: int,
        title: str,
        memory_date: date,
    ) -> bool:
        """Проверяет, есть ли уже у пары такое воспоминание."""
        stmt = (
            select(func.count())
            .select_from(Memory)
            .where(
                Memory.couple_id == couple_id,
                func.lower(Memory.title) == title.lower(),
                Memory.memory_date == memory_date,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def get_anniversaries_today(self, today: date) -> list[Memory]:
        """
        Возвращает годовщины, которые нужно напомнить сегодня.

        Условия:
        - месяц и день совпадают с сегодняшним днём;
        - год события меньше текущего года;
        - напоминание ещё не отправлялось сегодня;
        - пара активна.
        """
        stmt = (
            select(Memory)
            .join(Couple, Memory.couple_id == Couple.id)
            .where(
                Couple.status == "active",
                extract("month", Memory.memory_date) == today.month,
                extract("day", Memory.memory_date) == today.day,
                extract("year", Memory.memory_date) < today.year,
                or_(
                    Memory.last_notified.is_(None),
                    Memory.last_notified != today,
                ),
            )
            .order_by(Memory.memory_date.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_notified(self, memory_id: int, notified_date: date) -> None:
        """Отмечает, что напоминание за эту дату уже было отправлено."""
        stmt = (
            update(Memory)
            .where(Memory.id == memory_id)
            .values(last_notified=notified_date)
        )
        await self.session.execute(stmt)
        await self.session.flush()


    async def count_by_couple(self, couple_id: int) -> int:
        """Возвращает количество воспоминаний у пары."""
        stmt = (
            select(func.count())
            .select_from(Memory)
            .where(Memory.couple_id == couple_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()


    async def get_anniversaries_for_couple_on_date(
        self,
        couple_id: int,
        today: date,
    ) -> list[Memory]:
        """
        Возвращает годовщины пары, которые нужно поздравить сегодня.

        Условия:
        - месяц и день совпадают с сегодняшним днём;
        - год события меньше текущего года;
        - уведомление за сегодня ещё не отправлялось.
        """
        stmt = (
            select(Memory)
            .where(
                Memory.couple_id == couple_id,
                extract("month", Memory.memory_date) == today.month,
                extract("day", Memory.memory_date) == today.day,
                extract("year", Memory.memory_date) < today.year,
                or_(
                    Memory.last_notified.is_(None),
                    Memory.last_notified != today,
                ),
            )
            .order_by(Memory.memory_date.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())