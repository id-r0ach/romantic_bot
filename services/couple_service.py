import secrets
import string
from datetime import datetime, time, timedelta, timezone

from sqlalchemy.exc import IntegrityError

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from database.models.couple import Couple
from database.repositories.couple import CoupleRepository
from database.repositories.user import UserRepository
from services.letter_service import LetterService
from services.reason_service import ReasonGiftService


class CoupleService:
    def __init__(
        self,
        couple_repo: CoupleRepository,
        letter_service: LetterService,
        user_repo: UserRepository,
        bot: Bot,
        reason_service: ReasonGiftService | None = None,
    ) -> None:
        self.couple_repo = couple_repo
        self.letter_service = letter_service
        self.user_repo = user_repo
        self.bot = bot
        self.reason_service = reason_service

    @staticmethod
    def _generate_invite_code() -> str:
        """Генерация 6-символьного кода без неоднозначных символов"""
        alphabet = (
            string.ascii_uppercase.replace("O", "").replace("I", "").replace("L", "")
        )
        alphabet += string.digits.replace("0", "").replace("1", "")
        return "".join(secrets.choice(alphabet) for _ in range(6))

    async def create_couple(self, user_id: int) -> Couple:
        """Создать новую пару или обновить код в pending-паре"""
        existing = await self.couple_repo.get_by_user_id(user_id)
        if existing:
            raise ValueError("Ты уже в паре")

        user = await self.user_repo.get_by_tg_id(user_id)
        anniversary_tz = user.timezone if user and user.timezone else "UTC"

        invite_code = self._generate_invite_code()
        invite_expires = datetime.now(timezone.utc) + timedelta(hours=24)

        pending = await self.couple_repo.get_pending_by_user_id(user_id)

        if pending:
            try:
                return await self.couple_repo.update_invite_code(
                    couple_id=pending.id,
                    invite_code=invite_code,
                    invite_expires=invite_expires,
                    anniversary_tz=anniversary_tz,
                )
            except IntegrityError:
                raise ValueError("Не удалось создать код. Попробуй ещё раз")

        try:
            return await self.couple_repo.create_couple(
                user1_id=user_id,
                invite_code=invite_code,
                invite_expires=invite_expires,
                anniversary_tz=anniversary_tz,
            )
        except IntegrityError:
            raise ValueError("Не удалось создать код. Попробуй ещё раз")

    async def join_couple(self, user_id: int, invite_code: str) -> Couple:
        """Присоединиться к паре по коду"""
        existing = await self.couple_repo.get_by_user_id(user_id)
        if existing:
            raise ValueError("Ты уже в паре")

        couple = await self.couple_repo.get_by_invite_code(invite_code)
        if not couple:
            raise ValueError("Код не найден")

        if couple.invite_expires < datetime.now(timezone.utc):
            raise ValueError("Код истёк")

        if couple.user1_id == user_id:
            raise ValueError("Нельзя присоединиться к самому себе")

        activated = await self.couple_repo.activate_couple(couple.id, user_id)

        # Если пользователь до этого создавал свою pending-пару — отменяем её
        await self.couple_repo.cancel_pending_by_user(user_id)

        return activated

    async def get_couple(self, user_id: int) -> Couple | None:
        """Получить активную пару пользователя"""
        return await self.couple_repo.get_by_user_id(user_id)

    async def update_anniversary_time(self, user_id: int, new_time: time) -> None:
        """Обновить время напоминаний о годовщинах."""
        couple = await self.get_couple(user_id)
        if not couple:
            raise ValueError("Ты не в паре")
        await self.couple_repo.update_anniversary_time(couple.id, new_time)
        await self.couple_repo.session.commit()

    async def leave_couple(self, user_id: int) -> None:
        """Выйти из пары"""
        couple = await self.couple_repo.get_by_user_id(user_id)
        if not couple:
            raise ValueError("Ты не в паре")

        # 1. Разрываем пару
        await self.couple_repo.break_couple(couple.id)

        # 2. Отменяем все активные письма
        await self.letter_service.cancel_pending_letters(couple.id)

        # 3. Отменяем все подарки: черновики и активные
        if self.reason_service:
            await self.reason_service.cancel_gifts_for_couple(couple.id)

        # 4. Уведомляем партнера
        partner_id = (
            couple.user2_id if couple.user1_id == user_id else couple.user1_id
        )

        if partner_id:
            try:
                await self.bot.send_message(
                    chat_id=partner_id,
                    text="💔 Твой партнер решил завершить отношения. Пара распалась.",
                )
            except TelegramBadRequest:
                pass  # Партнер мог заблокировать бота