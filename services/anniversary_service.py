import logging
from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from database.models.couple import Couple
from database.models.memory import Memory
from database.repositories.couple import CoupleRepository
from database.repositories.memory import MemoryRepository

logger = logging.getLogger(__name__)


class AnniversaryService:
    def __init__(
        self,
        memory_repo: MemoryRepository,
        couple_repo: CoupleRepository,
        bot: Bot,
    ) -> None:
        self._memory_repo = memory_repo
        self._couple_repo = couple_repo
        self._bot = bot

    def _get_timezone(self, tz_name: str):
        """Возвращает часовой пояс или UTC как fallback."""
        try:
            return ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            return timezone.utc

    @staticmethod
    def _format_years(years: int) -> str:
        """
        Форматирует количество лет.

        Примеры:
            1 год
            2 года
            5 лет
            21 год
            22 года
            25 лет
        """
        if years % 100 in (11, 12, 13, 14):
            return f"{years} лет"

        if years % 10 == 1:
            return f"{years} год"

        if years % 10 in (2, 3, 4):
            return f"{years} года"

        return f"{years} лет"

    def _build_message(self, memories: list[Memory], today: datetime) -> str:
        """
        Собирает одно сообщение для всех годовщин пары.
        """
        lines = ["❤️ <b>Сегодня годовщина!</b>"]

        for memory in memories:
            years = today.year - memory.memory_date.year
            years_text = self._format_years(years)
            title = escape(memory.title)
            lines.append(f"📖 «{title}» — {years_text}")

        return "\n".join(lines)

    async def check_and_notify(self, now_utc: datetime) -> None:
        """
        Проверяет, нужно ли отправить напоминание о годовщине.

        Логика:
        - берём все активные пары;
        - переводим текущий момент в часовой пояс пары;
        - если время уже >= anniversary_time, проверяем годовщины;
        - если есть годовщины сегодня и они ещё не уведомлены — отправляем;
        - помечаем last_notified сегодняшней датой.
        """
        couples = await self._couple_repo.get_active_couples()

        for couple in couples:
            tz = self._get_timezone(couple.anniversary_tz)
            local_now = now_utc.astimezone(tz)

            # Если время напоминания ещё не наступило — пропускаем.
            if local_now.time() < couple.anniversary_time:
                continue

            today = local_now.date()

            memories = await self._memory_repo.get_anniversaries_for_couple_on_date(
                couple_id=couple.id,
                today=today,
            )

            if not memories:
                continue

            text = self._build_message(memories, local_now)

            recipients: list[int] = [couple.user1_id]

            if couple.user2_id is not None:
                recipients.append(couple.user2_id)

            for chat_id in recipients:
                try:
                    await self._bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        parse_mode="HTML",
                    )
                except TelegramBadRequest as e:
                    logger.warning(
                        f"Не удалось отправить годовщину пользователю {chat_id}: {e}"
                    )

            for memory in memories:
                await self._memory_repo.mark_notified(memory.id, today)

            logger.info(
                f"Отправлено напоминание о годовщине для пары {couple.id}: "
                f"{len(memories)} событий"
            )