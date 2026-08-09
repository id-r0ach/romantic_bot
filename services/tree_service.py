import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from database.models.couple import Couple
from database.repositories.couple import CoupleRepository
from database.repositories.letter import LetterRepository
from database.repositories.memory import MemoryRepository
from database.repositories.tree import TreeRepository

logger = logging.getLogger(__name__)

XP_PER_MEMORY = 10
XP_PER_DELIVERED_LETTER = 5

# Формат: (уровень, порог XP, эмодзи, название)
LEVELS: list[tuple[int, int, str, str]] = [
    (1, 0, "🌱", "Росток"),
    (2, 50, "🌿", "Саженец"),
    (3, 150, "🌳", "Дерево"),
    (4, 300, "🌸", "Цветущее"),
    (5, 500, "🌺", "Цветущее дерево"),
    (6, 800, "🍎", "Плодовое"),
    (7, 1200, "🌈", "Волшебное"),
]


class TreeService:
    def __init__(
        self,
        tree_repo: TreeRepository,
        couple_repo: CoupleRepository,
        memory_repo: MemoryRepository,
        letter_repo: LetterRepository,
        bot: Bot,
    ) -> None:
        self._tree_repo = tree_repo
        self._couple_repo = couple_repo
        self._memory_repo = memory_repo
        self._letter_repo = letter_repo
        self._bot = bot

    @staticmethod
    def calculate_level(total_xp: int) -> tuple[int, str, str]:
        """
        Возвращает уровень дерева по общему XP.

        Формат:
            (номер уровня, эмодзи, название)
        """
        level_number, _, emoji, name, _ = TreeService._level_info(total_xp)
        return level_number, emoji, name

    @staticmethod
    def get_level_display(level_number: int) -> tuple[str, str]:
        """
        Возвращает эмодзи и название уровня по номеру уровня.
        """
        for level, _, emoji, name in LEVELS:
            if level == level_number:
                return emoji, name

        return LEVELS[0][2], LEVELS[0][3]

    @staticmethod
    def _level_info(total_xp: int) -> tuple[int, int, str, str, int | None]:
        """
        Возвращает полную информацию об уровне.

        Формат:
            (
                номер уровня,
                порог XP текущего уровня,
                эмодзи,
                название,
                порог XP следующего уровня или None,
            )
        """
        current_level = LEVELS[0]
        next_level = None

        for level in LEVELS:
            if total_xp >= level[1]:
                current_level = level

        for level in LEVELS:
            if total_xp < level[1]:
                next_level = level
                break

        return (
            current_level[0],
            current_level[1],
            current_level[2],
            current_level[3],
            next_level[1] if next_level else None,
        )

    def _get_couple_tz(self, couple: Couple):
        """Возвращает часовой пояс пары или UTC как fallback."""
        try:
            return ZoneInfo(couple.anniversary_tz)
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            return timezone.utc

    def _days_together(self, couple: Couple) -> int:
        """Считает количество дней вместе."""
        if not couple.activated_at:
            return 0

        tz = self._get_couple_tz(couple)

        activated_at = couple.activated_at
        if activated_at.tzinfo is None:
            activated_at = activated_at.replace(tzinfo=timezone.utc)

        activated_date = activated_at.astimezone(tz).date()
        today = datetime.now(tz).date()

        days = (today - activated_date).days
        return max(days, 0)

    async def add_xp(
        self,
        couple_id: int,
        amount: int,
        reason: str,
    ) -> tuple[int, int]:
        """
        Добавляет XP дереву пары.

        Возвращает:
            (старый уровень, новый уровень)

        Если уровень не изменился, значения будут одинаковыми.
        Если уровень вырос — отправляет уведомление обоим партнёрам.
        """
        couple = await self._couple_repo.get_by_id(couple_id)

        if not couple:
            raise ValueError("Пара не найдена")

        tree = await self._tree_repo.get_or_create(couple_id)
        days_together = self._days_together(couple)

        old_total_xp = tree.xp + days_together
        old_level, _, _ = self.calculate_level(old_total_xp)

        # Если пара не активна или XP <= 0, ничего не начисляем.
        if amount <= 0 or couple.status != "active":
            return old_level, old_level

        new_tree = await self._tree_repo.add_xp(couple_id, amount)

        new_total_xp = new_tree.xp + days_together
        new_level, _, _ = self.calculate_level(new_total_xp)

        logger.info(
            "Tree XP update: couple_id=%s reason=%s old_total=%s new_total=%s old_level=%s new_level=%s",
            couple_id,
            reason,
            old_total_xp,
            new_total_xp,
            old_level,
            new_level,
        )

        if new_level > old_level:
            await self._notify_level_up(couple, new_level)

        return old_level, new_level

    async def _notify_level_up(self, couple: Couple, new_level: int) -> None:
        """Отправляет уведомление о новом уровне дерева обоим партнёрам."""
        emoji, name = self.get_level_display(new_level)

        text = (
            f"🌳 Ваше дерево выросло!\n"
            f"Теперь это {name} (уровень {new_level}) {emoji}"
        )

        recipients: list[int] = [couple.user1_id]

        if couple.user2_id is not None:
            recipients.append(couple.user2_id)

        for chat_id in recipients:
            try:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=text,
                )
            except TelegramBadRequest as e:
                logger.warning(
                    f"Не удалось отправить уведомление о росте дерева "
                    f"пользователю {chat_id}: {e}"
                )

    async def get_tree(self, couple_id: int) -> dict:
        """
        Возвращает данные дерева для экрана пары.
        """
        couple = await self._couple_repo.get_by_id(couple_id)

        if not couple:
            raise ValueError("Пара не найдена")

        tree = await self._tree_repo.get_or_create(couple_id)

        days_together = self._days_together(couple)

        memories_count = await self._memory_repo.count_by_couple(couple_id)
        letters_delivered_count = await self._letter_repo.count_delivered_by_couple(
            couple_id
        )

        total_xp = tree.xp + days_together

        (
            level_number,
            current_level_xp,
            level_emoji,
            level_name,
            next_level_xp,
        ) = self._level_info(total_xp)

        xp_to_next = 0
        if next_level_xp is not None:
            xp_to_next = max(next_level_xp - total_xp, 0)

        return {
            "couple_id": couple_id,
            "action_xp": tree.xp,
            "days_together": days_together,
            "total_xp": total_xp,
            "level": level_number,
            "emoji": level_emoji,
            "name": level_name,
            "current_level_xp": current_level_xp,
            "next_level_xp": next_level_xp,
            "xp_to_next": xp_to_next,
            "breakdown": {
                "days_xp": days_together,
                "memories_count": memories_count,
                "memories_xp": memories_count * XP_PER_MEMORY,
                "letters_delivered_count": letters_delivered_count,
                "letters_xp": letters_delivered_count * XP_PER_DELIVERED_LETTER,
            },
        }