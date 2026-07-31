import secrets
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError

from database.repositories.couple import CoupleRepository
from database.models.couple import Couple


class CoupleService:
    def __init__(self, couple_repo: CoupleRepository):
        self.couple_repo = couple_repo

    @staticmethod
    def _generate_invite_code() -> str:
        """Генерация 6-символьного кода без неоднозначных символов"""
        alphabet = string.ascii_uppercase.replace("O", "").replace("I", "").replace("L", "")
        alphabet += string.digits.replace("0", "").replace("1", "")
        return "".join(secrets.choice(alphabet) for _ in range(6))

    async def create_couple(self, user_id: int) -> Couple:
        """Создать новую пару и вернуть её с кодом"""
        # Проверяем, нет ли уже активной пары
        existing = await self.couple_repo.get_by_user_id(user_id)
        if existing:
            raise ValueError("Ты уже в паре")

        # Проверяем, нет ли pending пары (чтобы не создавать дубли)
        pending = await self.couple_repo.get_pending_by_user_id(user_id)
        if pending:
            return pending

        invite_code = self._generate_invite_code()
        invite_expires = datetime.now(timezone.utc) + timedelta(hours=24)

        try:
            couple = await self.couple_repo.create_couple(
                user1_id=user_id,
                invite_code=invite_code,
                invite_expires=invite_expires,
            )
            return couple
        except IntegrityError:
            # Редкий случай: код уже существует (почти невозможно)
            raise ValueError("Не удалось создать код. Попробуй ещё раз")

    async def join_couple(self, user_id: int, invite_code: str) -> Couple:
        """Присоединиться к паре по коду"""
        # Проверяем, не в паре ли уже пользователь
        existing = await self.couple_repo.get_by_user_id(user_id)
        if existing:
            raise ValueError("Ты уже в паре")

        # Ищем пару по коду
        couple = await self.couple_repo.get_by_invite_code(invite_code)
        if not couple:
            raise ValueError("Код не найден")

        # Проверяем срок действия
        if couple.invite_expires < datetime.now(timezone.utc):
            raise ValueError("Код истёк")

        # Проверяем, не свой ли это код
        if couple.user1_id == user_id:
            raise ValueError("Нельзя присоединиться к самому себе")

        # Активируем пару
        activated = await self.couple_repo.activate_couple(couple.id, user_id)
        return activated

    async def get_couple(self, user_id: int) -> Couple | None:
        """Получить активную пару пользователя"""
        return await self.couple_repo.get_by_user_id(user_id)

    async def leave_couple(self, user_id: int) -> None:
        """Выйти из пары"""
        couple = await self.couple_repo.get_by_user_id(user_id)
        if not couple:
            raise ValueError("Ты не в паре")

        await self.couple_repo.break_couple(couple.id)