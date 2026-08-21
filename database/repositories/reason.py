from datetime import datetime
from typing import Sequence

from sqlalchemy import delete as sa_delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.reason import Reason, ReasonGift, ReasonGiftStatus
from database.repositories.base import BaseRepository


class ReasonGiftRepository(BaseRepository[ReasonGift]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ReasonGift, session)

    async def create(self, gift: ReasonGift) -> ReasonGift:
        self.session.add(gift)
        await self.session.flush()
        return gift

    async def get_by_author(
        self,
        author_id: int,
        couple_id: int,
        statuses: Sequence[str],
    ) -> ReasonGift | None:
        """Ищет подарок автора в паре по списку статусов (например, draft или active)."""
        stmt = (
            select(ReasonGift)
            .where(
                ReasonGift.author_id == author_id,
                ReasonGift.couple_id == couple_id,
                ReasonGift.status.in_(statuses),
            )
            .order_by(ReasonGift.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_for_recipient(
        self,
        recipient_id: int,
        couple_id: int,
    ) -> ReasonGift | None:
        """Ищет активный (подаренный) подарок для получателя."""
        stmt = select(ReasonGift).where(
            ReasonGift.recipient_id == recipient_id,
            ReasonGift.couple_id == couple_id,
            ReasonGift.status == ReasonGiftStatus.ACTIVE,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_gifts_for_couple(self, couple_id: int) -> list[ReasonGift]:
        """Возвращает все draft и active подарки пары (нужно для отмены при расставании)."""
        stmt = select(ReasonGift).where(
            ReasonGift.couple_id == couple_id,
            ReasonGift.status.in_([ReasonGiftStatus.DRAFT, ReasonGiftStatus.ACTIVE]),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self, 
        gift_id: int, 
        status: str, 
        activated_at: datetime | None = None
    ) -> None:
        values: dict = {"status": status}
        if activated_at is not None:
            values["activated_at"] = activated_at
        
        stmt = update(ReasonGift).where(ReasonGift.id == gift_id).values(**values)
        await self.session.execute(stmt)
        await self.session.flush()

    async def update_last_opened(self, gift_id: int, now: datetime) -> None:
        stmt = (
            update(ReasonGift)
            .where(ReasonGift.id == gift_id)
            .values(last_opened_at=now)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def update_last_reminded(self, gift_id: int, now: datetime) -> None:
        """Обновляет время последнего напоминания (для APScheduler)."""
        stmt = (
            update(ReasonGift)
            .where(ReasonGift.id == gift_id)
            .values(last_reminded_at=now)
        )
        await self.session.execute(stmt)
        await self.session.flush()
    
    async def get_active_by_couple(self, couple_id: int) -> list[ReasonGift]:
        """Все активные подарки пары (в обе стороны)."""
        stmt = select(ReasonGift).where(
            ReasonGift.couple_id == couple_id,
            ReasonGift.status == ReasonGiftStatus.ACTIVE,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ReasonRepository(BaseRepository[Reason]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Reason, session)

    async def create(self, reason: Reason) -> Reason:
        self.session.add(reason)
        await self.session.flush()
        return reason

    async def get_by_gift(self, gift_id: int) -> list[Reason]:
        stmt = (
            select(Reason)
            .where(Reason.gift_id == gift_id)
            .order_by(Reason.position.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_next_unopened(self, gift_id: int) -> Reason | None:
        stmt = (
            select(Reason)
            .where(
                Reason.gift_id == gift_id,
                Reason.opened == False,  # noqa: E712
            )
            .order_by(Reason.position.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_gift(self, gift_id: int) -> int:
        stmt = select(func.count()).select_from(Reason).where(Reason.gift_id == gift_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_opened_by_gift(self, gift_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Reason)
            .where(
                Reason.gift_id == gift_id,
                Reason.opened == True,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_by_gift(self, gift_id: int) -> None:
        stmt = sa_delete(Reason).where(Reason.gift_id == gift_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def mark_opened(self, reason_id: int, now: datetime) -> None:
        stmt = (
            update(Reason)
            .where(Reason.id == reason_id)
            .values(opened=True, opened_at=now)
        )
        await self.session.execute(stmt)
        await self.session.flush()