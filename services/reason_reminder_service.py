import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from database.models.reason import ReasonGift
from database.repositories.couple import CoupleRepository
from database.repositories.reason import (
    ReasonGiftRepository,
    ReasonRepository,
)
from database.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class ReasonReminderService:
    """Ежедневное напоминание получателю, что причина ждёт."""

    def __init__(
        self,
        reason_gift_repo: ReasonGiftRepository,
        reason_repo: ReasonRepository,
        couple_repo: CoupleRepository,
        user_repo: UserRepository,
        bot: Bot,
    ) -> None:
        self._reason_gift_repo = reason_gift_repo
        self._reason_repo = reason_repo
        self._couple_repo = couple_repo
        self._user_repo = user_repo
        self._bot = bot

    @staticmethod
    def _get_timezone(tz_name: str):
        try:
            return ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            return timezone.utc

    @staticmethod
    def _is_today(dt: datetime | None, tz) -> bool:
        """Проверяет, попадает ли dt на «сегодня» в указанном поясе."""
        if dt is None:
            return False
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(tz).date() == datetime.now(tz).date()

    async def check_and_notify(self, now_utc: datetime) -> None:
        """Проходит по активным парам и шлёт напоминания, если пора."""
        couples = await self._couple_repo.get_active_couples()
        for couple in couples:
            couple_tz = self._get_timezone(couple.anniversary_tz)
            local_now = now_utc.astimezone(couple_tz)

            # Время ежедневных уведомлений пары ещё не наступило
            if local_now.time() < couple.anniversary_time:
                continue

            gifts = await self._reason_gift_repo.get_active_by_couple(
                couple.id
            )
            for gift in gifts:
                await self._maybe_remind(gift, now_utc)

    async def _maybe_remind(
        self,
        gift: ReasonGift,
        now_utc: datetime,
    ) -> None:
        recipient = await self._user_repo.get_by_tg_id(gift.recipient_id)

        # У получателя выключены уведомления — не spamим
        if recipient is not None and not recipient.notifications:
            return

        recipient_tz = self._get_timezone(
            recipient.timezone if recipient else "UTC"
        )

        # Сегодня уже открывал — напоминание не нужно
        if self._is_today(gift.last_opened_at, recipient_tz):
            return

        # Сегодня уже напоминали — не шлём повторно (идемпотентность)
        if self._is_today(gift.last_reminded_at, recipient_tz):
            return

        next_reason = await self._reason_repo.get_next_unopened(gift.id)
        if next_reason is None:
            return

        # Локальный импорт, чтобы избежать циклических зависимостей
        from bot.keyboards.reason_kb import get_reason_recipient_kb

        try:
            await self._bot.send_message(
                chat_id=gift.recipient_id,
                text="💌 Твоя причина на сегодня ждёт ❤️",
                reply_markup=get_reason_recipient_kb(
                    can_open=True,
                    next_position=next_reason.position,
                ),
            )
        except TelegramBadRequest as e:
            logger.warning(
                f"Не удалось отправить напоминание о причинах "
                f"пользователю {gift.recipient_id}: {e}"
            )

        # Отмечаем в любом случае, чтобы не слать повторно
        # (например, если бот заблокирован)
        await self._reason_gift_repo.update_last_reminded(gift.id, now_utc)
        logger.info(
            f"Отправлено напоминание о причинах для подарка {gift.id} "
            f"пользователю {gift.recipient_id}"
        )