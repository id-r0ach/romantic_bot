from datetime import datetime

from sqlalchemy import select, update

from database.models.letter import Letter
from database.repositories.base import BaseRepository


class LetterRepository(BaseRepository[Letter]):
    
    def __init__(self, session) -> None:
        super().__init__(Letter, session)

    async def create(self, letter: Letter) -> Letter:
        """Создаёт письмо и возвращает его с проставленным id."""
        self.session.add(letter)
        await self.session.flush()
        return letter

    async def get_pending(self, now: datetime) -> list[Letter]:
        """Находит все письма, которые пора доставить."""
        query = select(Letter).where(
            Letter.status == "pending",
            Letter.open_date <= now
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_delivered(self, letter_id: int, delivered_at: datetime) -> None:
        """Помечает письмо как доставленное."""
        query = (
            update(Letter)
            .where(Letter.id == letter_id)
            .values(status="delivered", delivered_at=delivered_at)
        )
        await self.session.execute(query)
        await self.session.flush()

    async def cancel_by_couple(self, couple_id: int) -> None:
        """Отменяет все активные письма пары при разрыве."""
        query = (
            update(Letter)
            .where(Letter.couple_id == couple_id, Letter.status == "pending")
            .values(status="cancelled")
        )
        await self.session.execute(query)
        await self.session.flush()

    async def get_active_by_user(self, user_id: int) -> list[Letter]:
        """Получает все не отправленные и не отмененные письма пользователя."""
        query = select(Letter).where(
            Letter.sender_id == user_id,
            Letter.status == "pending"
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())