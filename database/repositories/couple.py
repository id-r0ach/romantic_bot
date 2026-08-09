from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.couple import Couple
from database.repositories.base import BaseRepository


class CoupleRepository(BaseRepository[Couple]):
    def __init__(self, session: AsyncSession):
        super().__init__(Couple, session)

    async def create_couple(
        self,
        user1_id: int,
        invite_code: str,
        invite_expires: datetime,
        anniversary_tz: str = "UTC",
    ) -> Couple:
        """Создать новую пару (статус pending)"""
        couple = Couple(
            user1_id=user1_id,
            user2_id=None,
            status="pending",
            invite_code=invite_code,
            invite_expires=invite_expires,
            anniversary_tz=anniversary_tz,
        )
        self.session.add(couple)
        await self.session.flush()  # чтобы получить id
        return couple

    async def get_by_user_id(self, user_id: int) -> Couple | None:
        """Найти активную пару по ID пользователя (как user1 или user2)"""
        query = select(Couple).where(
            Couple.status == "active",
            ((Couple.user1_id == user_id) | (Couple.user2_id == user_id)),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_by_user_id(self, user_id: int) -> Couple | None:
        """Найти pending пару создателя (чтобы показать код)"""
        query = select(Couple).where(
            Couple.user1_id == user_id,
            Couple.status == "pending",
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_invite_code(self, invite_code: str) -> Couple | None:
        """Найти пару по коду приглашения"""
        query = select(Couple).where(
            Couple.invite_code == invite_code,
            Couple.status == "pending",
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def activate_couple(self, couple_id: int, user2_id: int) -> Couple:
        """Активировать пару (присоединить второго пользователя)"""
        query = (
            update(Couple)
            .where(Couple.id == couple_id)
            .values(
                user2_id=user2_id,
                status="active",
                activated_at=datetime.now(timezone.utc),
            )
            .returning(Couple)
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.scalar_one()

    async def break_couple(self, couple_id: int) -> None:
        """Завершить пару (статус broken)"""
        query = (
            update(Couple)
            .where(Couple.id == couple_id)
            .values(status="broken")
        )
        await self.session.execute(query)

    async def update_invite_code(
        self,
        couple_id: int,
        invite_code: str,
        invite_expires: datetime,
        anniversary_tz: str | None = None,
    ) -> Couple:
        """Обновить код приглашения в pending-паре"""
        values: dict = {
            "invite_code": invite_code,
            "invite_expires": invite_expires,
        }

        if anniversary_tz is not None:
            values["anniversary_tz"] = anniversary_tz

        query = (
            update(Couple)
            .where(
                Couple.id == couple_id,
                Couple.status == "pending",
            )
            .values(**values)
            .returning(Couple)
        )
        result = await self.session.execute(query)
        await self.session.flush()
        return result.scalar_one()

    async def cancel_pending_by_user(self, user_id: int) -> None:
        """Отменить pending-пары пользователя, где он является создателем"""
        query = (
            update(Couple)
            .where(
                Couple.user1_id == user_id,
                Couple.status == "pending",
            )
            .values(status="cancelled")
        )
        await self.session.execute(query)
        await self.session.flush()


    async def get_active_couples(self) -> list[Couple]:
        """Возвращает все активные пары."""
        query = select(Couple).where(Couple.status == "active")
        result = await self.session.execute(query)
        return list(result.scalars().all())