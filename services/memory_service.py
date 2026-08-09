import logging
from datetime import date, datetime, timezone

from database.models.memory import Memory
from database.repositories.couple import CoupleRepository
from database.repositories.memory import MemoryRepository
from services.tree_service import TreeService, XP_PER_MEMORY

logger = logging.getLogger(__name__)


class MemoryService:
    def __init__(
        self,
        memory_repo: MemoryRepository,
        couple_repo: CoupleRepository,
        tree_service: TreeService,
    ) -> None:
        self._memory_repo = memory_repo
        self._couple_repo = couple_repo
        self._tree_service = tree_service

    async def create_memory(
        self,
        couple_id: int,
        author_id: int,
        title: str,
        description: str | None,
        memory_date: date,
    ) -> Memory:
        """Создаёт воспоминание и начисляет XP дереву пары."""
        title = title.strip()

        if not title:
            raise ValueError("Введи название")

        if len(title) > 120:
            raise ValueError("Название слишком длинное, максимум 120 символов")

        if description is not None:
            description = description.strip()
            if not description:
                description = None

        today = datetime.now(timezone.utc).date()

        if memory_date > today:
            raise ValueError("Дата должна быть в прошлом")

        is_duplicate = await self._memory_repo.exists_by_title_and_date(
            couple_id=couple_id,
            title=title,
            memory_date=memory_date,
        )

        if is_duplicate:
            raise ValueError("Такое воспоминание уже добавлено")

        memory = Memory(
            couple_id=couple_id,
            author_id=author_id,
            title=title,
            description=description,
            memory_date=memory_date,
        )

        created_memory = await self._memory_repo.create(memory)

        try:
            await self._tree_service.add_xp(
                couple_id=couple_id,
                amount=XP_PER_MEMORY,
                reason="memory_created",
            )
        except Exception as e:
            # Воспоминание уже создано.
            # Если начисление XP упадёт, не теряем пользовательские данные.
            logger.error(f"Не удалось начислить XP за воспоминание: {e}")

        return created_memory

    async def get_memories(self, couple_id: int) -> list[Memory]:
        """Возвращает все воспоминания пары."""
        return await self._memory_repo.get_by_couple(couple_id)

    async def get_memory(self, memory_id: int) -> Memory | None:
        """Возвращает воспоминание по ID."""
        return await self._memory_repo.get_by_id(memory_id)

    async def delete_memory(self, memory_id: int, user_id: int) -> None:
        """Удаляет воспоминание, если пользователь состоит в этой паре."""
        memory = await self._memory_repo.get_by_id(memory_id)

        if not memory:
            raise ValueError("Воспоминание не найдено")

        couple = await self._couple_repo.get_by_user_id(user_id)

        if not couple or couple.id != memory.couple_id:
            raise ValueError("Нет доступа к этому воспоминанию")

        await self._memory_repo.delete_by_id(memory_id)