import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from bot.utils.timezone_utils import to_local
from database.models.letter import Letter
from database.repositories.letter import LetterRepository
from database.repositories.user import UserRepository
from services.tree_service import TreeService, XP_PER_DELIVERED_LETTER

logger = logging.getLogger(__name__)


class LetterService:
    def __init__(
        self,
        letter_repo: LetterRepository,
        user_repo: UserRepository,
        bot: Bot,
        tree_service: TreeService,
    ) -> None:
        self._letter_repo = letter_repo
        self._user_repo = user_repo
        self._bot = bot
        self._tree_service = tree_service

    async def create_letter(
        self,
        couple_id: int,
        sender_id: int,
        receiver_id: int,
        text: str,
        open_date: datetime,
    ) -> Letter:
        """Создаёт новое письмо."""
        letter = Letter(
            couple_id=couple_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            text=text,
            open_date=open_date,
            status="pending",
        )
        return await self._letter_repo.create(letter)

    async def get_pending_letters(self, now: datetime) -> list[Letter]:
        """Возвращает все письма, которые пора доставить."""
        return await self._letter_repo.get_pending(now)

    async def get_letter_by_id(self, letter_id: int) -> Letter | None:
        """Получает письмо по ID."""
        return await self._letter_repo.get_by_id(letter_id)

    async def deliver_letter(self, letter: Letter) -> None:
        """Отправляет письмо, обновляет БД, начисляет XP и уведомляет отправителя."""
        sender = await self._user_repo.get_by_tg_id(letter.sender_id)
        receiver = await self._user_repo.get_by_tg_id(letter.receiver_id)

        sender_name = (
            sender.first_name or sender.username or "Твой партнер"
            if sender
            else "Твой партнер"
        )
        receiver_name = (
            receiver.first_name or receiver.username or "партнер"
            if receiver
            else "партнер"
        )

        receiver_tz = receiver.timezone if receiver else "UTC"
        sender_tz = sender.timezone if sender else "UTC"

        # 1. Отправляем письмо получателю с кнопками
        try:
            created_local = to_local(letter.created_at, receiver_tz)
            opened_local = to_local(letter.open_date, receiver_tz)

            # Импортируем клавиатуру здесь, чтобы избежать циклических импортов
            from bot.keyboards.letter_delivery_kb import get_letter_delivery_kb

            await self._bot.send_message(
                chat_id=letter.receiver_id,
                text=(
                    "💌 <b>Письмо из капсулы времени!</b>\n"
                    f"От: {sender_name}\n"
                    f"Дата написания: {created_local.strftime('%d.%m.%Y')}\n"
                    f"Дата открытия: {opened_local.strftime('%d.%m.%Y в %H:%M')}\n"
                    f"✨ <i>{letter.text}</i>"
                ),
                reply_markup=get_letter_delivery_kb(letter.id),
                parse_mode="HTML",
            )
        except TelegramBadRequest as e:
            logger.warning(
                f"Не удалось доставить письмо {letter.id} "
                f"пользователю {letter.receiver_id}: {e}"
            )

        # 2. Помечаем письмо как доставленное в БД
        await self._letter_repo.mark_delivered(
            letter.id,
            datetime.now(timezone.utc),
        )

        # 3. Начисляем XP дереву пары за доставку письма
        try:
            await self._tree_service.add_xp(
                couple_id=letter.couple_id,
                amount=XP_PER_DELIVERED_LETTER,
                reason="letter_delivered",
            )
        except Exception as e:
            # Письмо уже доставлено.
            # Если начисление XP упадёт, не теряем доставку письма.
            logger.error(f"Не удалось начислить XP за доставку письма: {e}")

        # 4. Уведомляем отправителя
        try:
            delivered_local = to_local(datetime.now(timezone.utc), sender_tz)

            await self._bot.send_message(
                chat_id=letter.sender_id,
                text=(
                    f"💌 Твоё письмо для {receiver_name} было доставлено!\n"
                    f"📅 {delivered_local.strftime('%d.%m.%Y в %H:%M')}"
                ),
            )
        except TelegramBadRequest as e:
            logger.warning(
                f"Не удалось уведомить отправителя {letter.sender_id} "
                f"о письме {letter.id}: {e}"
            )

    async def cancel_pending_letters(self, couple_id: int) -> None:
        """Отменяет все активные письма пары при разрыве."""
        await self._letter_repo.cancel_by_couple(couple_id)

    async def get_active_letters(self, user_id: int) -> list[Letter]:
        """Возвращает все ожидающие письма пользователя."""
        return await self._letter_repo.get_active_by_user(user_id)